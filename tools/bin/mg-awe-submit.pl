#!/usr/bin/env perl

use strict;
use warnings;



#https://github.com/MG-RAST/Shock/blob/master/libs/shock.pm
use shock;
use awe;

use JSON;

use Data::Dumper;
use File::Basename;

use Getopt::Long;

my $shockurl = "http://shock1.chicago.kbase.us:80";
#my $shockurl = 'http://shock.metagenomics.anl.gov';

my $aweserverurl = "http://140.221.84.148:8000"; # Wei's server
my $clientgroup = 'qiime-wolfgang';

my $shocktoken=$ENV{'GLOBUSONLINE'} || ENV{'KB_AUTH_TOKEN'};

#purpose of wrapper: replace env variables, capture stdout and stderr and archive output directory
my @awe_job_states = ('in-progress', 'completed', 'queued', 'pending', 'deleted' , 'suspend' );







sub shock_upload {
	my ($shock) = shift(@_);
	my @other_args = @_;
	
	my $shock_data = $shock->upload(@other_args); # "test.txt"
	unless (defined $shock_data) {
		die;
	}
	#print Dumper($shock_data);
	unless (defined $shock_data->{'id'}) {
		die;
	}
	
	return $shock_data->{id};
}

sub wait_for_job {
	
	my ($awe, $job_id) = @_;
	
	my $jobstatus_hash;
	
	# TODO add time out ??
	while (1) {
		sleep(3);
		
		eval {
			$jobstatus_hash = $awe->getJobStatus($job_id);
		};
		if ($@) {
			print "error: getJobStatus $job_id\n";
			exit(1);
		}
		#print $json->pretty->encode( $jobstatus_hash )."\n";
		my $state = $jobstatus_hash->{data}->{state};
		print "state: $state\n";
		if ($state ne 'in-progress') {
			last;
		}
	}
	return $jobstatus_hash;
}



sub get_awe_output_nodes {
	my ($job_hash) = @_;
	
	my $output_nodes = {};
	foreach my $task (@{$job_hash->{tasks}}) {
		
		if (defined $task->{outputs}) {
			my $outputs = $task->{outputs};
			
			foreach my $resultfilename (keys(%$outputs)) {
				
				if (defined $output_nodes->{$resultfilename}) {
					die "error: output filename not unique ($resultfilename)";
				}
				
				$output_nodes->{$resultfilename} = $outputs->{$resultfilename};
			}
			
			
		}
	}
	#print Dumper($output_nodes);
	#exit(0);
	return $output_nodes;
}


sub download_ouput_from_shock{
	my ($shock, $output_nodes, $download_dir) = @_;
	
	my $download_success = 1 ;
	print Dumper($output_nodes);
	
	foreach my $resultfilename (keys(%$output_nodes)) {
		print "resultfilename: $resultfilename\n";
		
		my $download_name = $resultfilename;
		if (defined $download_dir ) {
			$download_name = $download_dir.'/'.$resultfilename;
		}
		
		if (-e $download_name) {
			print "$download_name already exists, refuse to overwrite...\n";
			exit(1);
		}
		
		my $result_obj = $output_nodes->{$resultfilename};
		unless (defined $result_obj) {
			die;
		}
		unless (ref($result_obj) eq 'HASH') {
			die;
		}
		
		
		
				
		my $result_node = $result_obj->{'node'};
		unless (defined $result_node) {
			die;
		}
		#my $result_size =  $result_obj->{size};
		
		#print Dumper($result_obj);
		
		
		
		if (defined $result_node) {
			#push(@temporary_shocknodes, $result_node);
			print "downloading $resultfilename...\n";
			$shock->download_to_path($result_node, $download_name);
			
		} else {
			print Dumper($result_obj);
			#exit(0);

			#print $json->pretty->encode( $jobstatus_hash )."\n";
			print STDERR "warning: no result found\n";
			$download_success=0;
			die;
		}
		
		
	}
	return $download_success;
}


sub delete_shock_nodes{
	my ($shock, $output_nodes) = @_;
	
	
	
	
	my $delete_ok = 1;
	foreach my $resultfilename (keys %$output_nodes) {
		
		my $result_obj = $output_nodes->{$resultfilename};
		my $node_to_be_deleted = $result_obj->{node};
		#my $result_size =  $result_obj->{size};
		
		if (defined $node_to_be_deleted) {
			
			# delete
			print "try to delete $node_to_be_deleted\n";
			
			my $nodeinfo = $shock->get_node($node_to_be_deleted);
			
			if (defined $nodeinfo) {
				#print Dumper($nodeinfo);
				
				my $deleteshock = $shock->delete($node_to_be_deleted);
				#print Dumper($deleteshock);
				
				unless (defined $deleteshock->{'status'} && $deleteshock->{'status'}==200) {
					print "error deleting $node_to_be_deleted\n";
					$delete_ok = 0;
				} else {
					print "deleted $node_to_be_deleted\n"
				}
			} else {
				print "error deleting node $node_to_be_deleted, node not found\n";
			}
			
		} else {
			#print $json->pretty->encode( $jobstatus_hash )."\n";
			print STDERR "warning: no result found\n";
			$delete_ok = 0;
		}
	}
	return $delete_ok;
}

sub download_and_delete_output_job_nodes {
	my ($job_hash, $shock) = @_;
	
	
	my $job_name = $job_hash->{'info'}->{'name'} || die;
	
	my $download_dir = ".";
	#my $download_dir = $job_name;
	#system("mkdir -p ".$download_dir);
	
	my $output_nodes = get_awe_output_nodes($job_hash);
	
	my $download_success = download_ouput_from_shock($shock, $output_nodes, $download_dir);
	
	
	if ($download_success == 0 ) {
		die "download failed";
	}
	
	
	### delete output shock nodes ####
	my $delete_ok = delete_shock_nodes($shock, $output_nodes);
	
	

	if ($delete_ok == 0) {
		return undef;
	} else {
		return 1;
	}
}


sub getCompletedJobs {
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	
	my $jobs = $awe->getJobQueue('info.clientgroups' => $clientgroup);
	
	#print Dumper($jobs);
	unless (defined $jobs) {
		die;
	}
	unless (defined $jobs->{data}) {
		die;
	}
	
	
	my @completed_jobs =() ;
	
	my $states={};
	$states->{$_}=0 for @awe_job_states;
	foreach my $job (@{$jobs->{data}}){
		$states->{lc($job->{state})}++;
		
		if (lc($job->{state}) eq 'completed') {
			push(@completed_jobs, $job);
		}
		#print "state: ".$job->{state}." user: ".$job->{info}->{user}."\n";
		
		#delete jobs
		if (0) {
			my $dd = $awe->deleteJob($job->{id});
			print Dumper($dd);
		}
		
	}
	
	print "\n** job states **\n";
	print "$_: ".($states->{$_}||'0')."\n" for @awe_job_states;
	if (keys($states) > 6) { # in case Wei introduces new states.. ;-)
		die;
	}
	return @completed_jobs;
}


sub get_jobs_and_cleanup {
	
	
	
	my $job_hash={};
	foreach my $job (@_) {
		$job_hash->{$job}=1;
	}
	my $jobs_to_process = @_;
	print "jobs_to_process: $jobs_to_process\n";
	
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	
	my $all_jobs = $awe->getJobQueue('info.clientgroups' => $clientgroup);
	
	#print Dumper($all_jobs);
	
	
	my $shock = new Shock($shockurl, $shocktoken); # shock production
	unless (defined $shock) {
		die;
	}
	
	
	my $job_deletion_ok= 1;
	foreach my $job_object (@{$all_jobs->{data}}) {
		
		my $job = $job_object->{'id'};
		
		unless (defined($job_hash->{$job})) {
			next;
		}
		
		#print "completed job $job\n";
		
		print Dumper($job_object)."\n";
		my $node_delete_status = download_and_delete_output_job_nodes($job_object, $shock);
		
		if (defined $node_delete_status) {
			print "deleting job ".$job_object->{id}."\n";
			my $dd = $awe->deleteJob($job_object->{id});
			print Dumper($dd);
		} else {
			$job_deletion_ok = 0;
		}
		$jobs_to_process--;
		
		
	}
	
	if ($jobs_to_process != 0 ) {
		die "not all jobs processed";
	}
	
	if ($job_deletion_ok == 1) {
		return 1;
	}
	
	return 0;
}

sub getAWE_results_and_cleanup {
	
	my @completed_jobs = getCompletedJobs();
	
	
	my $job_deletion_ok =  get_jobs_and_cleanup(@completed_jobs);
	
	
	if ($job_deletion_ok == 1) {
		return 1;
	}
	return undef;
}

sub showAWEstatus {
	
	my $mystate = shift(@_);
	unless (defined $mystate) {
		$mystate = 'completed';
	}
	
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	$awe->checkClientGroup($clientgroup);
	
	my $jobs = $awe->getJobQueue('info.clientgroups' => $clientgroup);
	
	#print Dumper($jobs);
	unless (defined $jobs) {
		die;
	}
	unless (defined $jobs->{data}) {
		die;
	}
	
	my @jobs = ();
	
	my $states={};
	$states->{$_}=0 for @awe_job_states;
	foreach my $job (@{$jobs->{data}}){
		$states->{lc($job->{state})}++;
		
		if (lc($job->{state}) eq lc($mystate)) {
			print Dumper($job);
			push(@jobs, $job->{id});
		}
		
	}
	
	if (@jobs > 0) {
		print "summary:\n";
		print join(' ' , @jobs)."\n";
	}
	
	print "\n** job states **\n";
	print "$_: ".($states->{$_}||'0')."\n" for @awe_job_states;
	if (keys($states) > 6) { # in case Wei introduces new states.. ;-)
		die;
	}
	
	return;
}

sub parse_command {
	
	my $command_str = shift(@_);
	
	
	
	
	print "COMMAND_a: ".$command_str."\n";
	my @COMMAND = split(/\s/, $command_str); # TODO need better way for this!?
	
	#print "split: ". join(',', @COMMAND)."\n";
	#exit(0);
	
	
	my @input_files_local=();
	my @output_files=();
	my @output_directories=();
	
	
	
	
	for (my $i=0; $i <@COMMAND ; ++$i) {
		
		if ($COMMAND[$i] =~ /^@@@/) {
			#print "at $ARGV[$i]\n";
			my $output_directory = substr($COMMAND[$i], 3);
			print "output_directory: $output_directory\n";
			push (@output_directories, $output_directory);
			$COMMAND[$i] = $output_directory; # need to encode info about directory in trojan script
		} elsif ($COMMAND[$i] =~ /^@@/) {
			#print "at $ARGV[$i]\n";
			my $output_file = substr($COMMAND[$i], 2);
			print "output_file: $output_file\n";
			if (-e $output_file) {
				print STDERR "error: output_file $output_file already exists\n";
				exit(1);
			}
			
			
			my $id = @output_files;
			push(@output_files, $output_file);
			$COMMAND[$i] = $output_file;
			#$COMMAND[$i] = '[OUTPUT'.$id.']';
		} elsif ($COMMAND[$i] =~ /^@/) {
			#print "at $ARGV[$i]\n";
			my $input_file = substr($COMMAND[$i], 1);
			print "input_file: $input_file\n";
			
			unless (-e $input_file) {
				print STDERR "error: file $input_file not found\n";
				exit(1);
			}
			
			my $id = @input_files_local;
			push(@input_files_local, $input_file);
			$COMMAND[$i] = '@[INPUT'.$id.']';
			#$COMMAND[$i] = '@'.basename($input_file);
			
			
		}
		
	}
	
	my $cmd = join(' ',@COMMAND);
	print "COMMAND_b: ".$cmd."\n";
	
	
	my $resulttarfile = 'x.tar';
	
	if (@output_directories > 0) {
		$resulttarfile = $output_directories[0];
		$resulttarfile =~ s/\///g;
		$resulttarfile.='.tar';
		
		if (-e $resulttarfile) {
			print STDERR $resulttarfile." already exists\n";
			exit(1);
		}
		
	}
	
	return (\@input_files_local , \@output_files, \@output_directories, $cmd);
}


sub generateAndSubmitSimpleAWEJob {
	my %h = @_;
	
	my $command = $h{'cmd'}; # example
	
	my $clientgroup = $h{'clientgroup'} || "qiime-wolfgang";
	my $awe_user = "awe_user";
	
	
	
	############################################
	# connect to AWE server and check the clients
	
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	#checkClients($awe, $clientgroup) == 0 or exit(1);
	
	
	############################################
	#connect to SHOCK server
	
	print "connect to SHOCK\n";
	my $shock = new Shock($shockurl, $shocktoken); # shock production
	unless (defined $shock) {
		die;
	}
	
	
	
	#parse input/output
	
	my ($input_files_local, $output_files, $output_directories, $command_parsed) = &parse_command($command);
	
	### create task template ###
	my $task_template={};
	$task_template->{'cmd'} = $command_parsed;
	for (my $i=0 ; $i < @{$input_files_local} ; ++$i ) {
		push(@{$task_template->{'inputs'}}, '[INPUT'.$i.']' );
	}
	
	for (my $i=0 ; $i < @{$output_files} ; ++$i ) {
		my $outputfile = $output_files->[$i];
		push(@{$task_template->{'outputs'}}, basename($outputfile) );
	}
	if (defined $h{'output_files'} ) {
		my @of = split(',', $h{'output_files'});
		foreach my $file (@of) {
			push(@{$task_template->{'outputs'}}, basename($file) );
		}
	
		$task_template->{'trojan'}->{'out_files'}=\@of;
	}
	
	print "generated template:\n";
	print Dumper($task_template);

		
	### create task (using the above generated template) ###
	my $task = {
		"task_id" => "single_task",
		#	#"task_cmd" => $command_parsed,
		"task_template" => "template",
		#"INPUT" => ["task", "0_pick_closed_reference_otus", "otu_table.biom"],
		#"INPUT" => ["shock", "[INPUT]", "input.fas"],
		#"OUTPUT" => "normalized.biom",
		"TROJAN" => ["shock", "[TROJAN1]", "trojan1.pl"]
	};

	
	my @inputs=();
	for (my $i=0 ; $i < @{$input_files_local} ; ++$i ) {
		my $inputfile = $input_files_local->[$i];
		$task->{'INPUT'.$i} = ["shock", "[INPUT".$i."]", $inputfile];
		push(@inputs, 'INPUT'.$i);
	}
	#$task->{'inputs'} = \@inputs;
	
	my @outputs=();
	for (my $i=0 ; $i < @{$output_files} ; ++$i ) {
		my $outputfile = $output_files->[$i];
		$task->{'OUTPUT'.$i} = $outputfile;
		push(@outputs, basename($outputfile));
		#print "push: ".basename($outputfile)."\n";
	}
	if (defined $h{'output_files'} ) {
		my @of = split(',', $h{'output_files'});
		foreach my $file (@of) {
			push(@{$task->{'outputs'}}, basename($file) );
		}
	}
	
	print "generated task (without input):\n";
	print Dumper($task);
	
	#exit(0);
	
	
	#$task->{'outputs'} = \@outputs;

	
	#my $task_tmpls={};
	#$task_tmpls->{'template'} = $task_template;
	
	
	#print "task:\n";
	#print Dumper($task);
	
	my $awe_qiime_job = AWE::Job->new(
		'info' => {
			"pipeline"=> "simple-autogen",
			"name"=> "simple-autogen-name",
			"project"=> "simple-autogen-prj",
			"user"=> $awe_user,
			"clientgroups"=> $clientgroup,
			"noretry"=> JSON::true
		},
		'shockhost' => $shockurl,
		'task_templates' => {'template' => $task_template}, # only one template in hash
		'tasks' => [$task]
	);
	
	
	
	### define job input ###
	my $job_input = {};
	
	if (defined $h{'output_files'} ) {
		my @of = split(',', $h{'output_files'});
		foreach my $file (@of) {
			push(@outputs, basename($file));
			print "push: ".basename($file)."\n";
		}
		$job_input->{'TROJAN1'}->{'data'} = AWE::Job::get_trojanhorse("out_files" => \@of) ;
	} else  {
		$job_input->{'TROJAN1'}->{'data'} = AWE::Job::get_trojanhorse() ;
	}
	#$job_input->{'TROJAN1'}->{'node'}= "fake_shock_node_trojan1";
	#$job_input->{'TROJAN1'}->{'shockhost'}= "fake_host";
	
	
		
	# local files to be uploaded
	for (my $i=0 ; $i < @{$input_files_local} ; ++$i ) {
		my $inputfile = $input_files_local->[$i];
		$job_input->{'INPUT'.$i}->{'file'} = $inputfile;
		#$job_input->{'INPUT'.$i}->{'node'} = "fake_shock_node".$i;
		#$job_input->{'INPUT'.$i}->{'shockhost'}= "fake_host";
	}
	
	

	
	
	#$job_input->{'INPUT-PARAMETER'}->{'file'} = './otu_picking_params_97.txt';   	  # local file to be uploaded
	
	#print Dumper($job_input);
		
	
	#upload job input files
	$shock->upload_temporary_files($job_input);
	
	
	# create job with the input defined above
	my $workflow = $awe_qiime_job->create(%$job_input);
	
	#exit(0);
	
	#overwrite jobname:
	#$workflow->{'info'}->{'name'} = $sample;
	
	my $json = JSON->new;
	print "AWE job ready for submission:\n".$json->pretty->encode( $workflow )."\n";
	
	print "submit job to AWE server...\n";
	my $submission_result = $awe->submit_job('json_data' => $json->encode($workflow));
	
	print "result from AWE server:\n".$json->pretty->encode( $submission_result )."\n";
	
	return;
}



########################################################################################
########################################################################################
########################################################################################
########################################################################################
# START

#if (-e $resultfilename) {
#	print STDERR "error: resultfile $resultfilename already exists\n";
#	exit(1);
#}



unless (@ARGV) {
	print "usage mg-awe-submit.pl --cmd=\"cmd args\"...\n";
	print "      mg-awe-submit.pl --status\n";
	print "      mg-awe-submit.pl --get\n";
	print "      mg-awe-submit.pl --delete jobids\n";
	print "      mg-awe-submit.pl --shock_query id_1,id_2..\n";
	print "      mg-awe-submit.pl --shock_clean\n";
	exit(0);
}


my $h = {};

GetOptions($h, 'cmd=s' , 'status', 'get_all', 'get_jobs=s' , 'delete=s' , 'shock_query=s' , 'shock_clean' , 'output_files=s');



if (defined($h->{"status"})) {
	showAWEstatus($ARGV[0]);
	exit(0);

} elsif (defined($h->{"delete"})) {
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	my @jobs = split(',', $h->{"delete"});
	foreach my $job (@jobs) {
		my $dd = $awe->deleteJob($job);
		print Dumper($dd);
	}
	exit(0);
} elsif (defined($h->{"shock_query"})) {
	
	
	my @queries = split(',', $h->{"shock_query"});
	
	my $shock = new Shock($shockurl, $shocktoken);
	unless (defined $shock) {
		die;
	}
	
	my $response =  $shock->query(@queries);
	print Dumper($response);
	exit(0);
	
} elsif (defined($h->{"shock_clean"})) {
	
	my $shock = new Shock($shockurl, $shocktoken);
	unless (defined $shock) {
		die;
	}
	#my $response = $shock->get_node('bfd36538-3715-4bd7-9351-e7268b06c05a');
	#print Dumper($response);
	#exit(0);
	
	my $response =  $shock->query('temporary' => '1');
	
	#my $response =  $shock->query('statistics.length_max' => 1175);
	print Dumper($response);
	
	my @list =();
	
	unless (defined $response->{'data'}) {
		die;
	}
	
	foreach my $node (@{$response->{'data'}}) {
		print $node->{'id'}."\n";
		push(@list, $node->{'id'});
	}
	
	foreach my $node (@list) {
		defined($shock->delete($node)) or die;
	}
	
	
	exit(0);

} elsif (defined($h->{"get_jobs"})) {
	
	my @jobs = split(/,/,$h->{"get_jobs"});
	
	get_jobs_and_cleanup(@jobs);
	
	print "done.\n";
	exit(0);
} elsif (defined($h->{"get_all"})) {
	getAWE_results_and_cleanup();
	print "done.\n";
	exit(0);
} elsif (defined($h->{"cmd"})) {
	
	my $cmd = $h->{"cmd"};
	my $output_files = $h->{"output_files"};
	
	my @moreopts=();
	if (defined $output_files) {
		@moreopts = ("output_files", $output_files);
	}
	
	
	#example:
	#./awe.pl --output_files=ucr/otu_table.biom --cmd="pick_closed_reference_otus.py -i @4506694.3.fas -o ucrC97 -p @otu_picking_params_97.txt -r /home/ubuntu/data/gg_13_5_otus/rep_set/97_otus.fasta"
	
	## compose AWE job ##
	generateAndSubmitSimpleAWEJob('cmd' => $cmd, @moreopts);
	
	
	
	exit(0);

}







#my $json = JSON->new;

# example
#./awe.pl pick_closed_reference_otus.py -i @100.preprocess.passed.fna -o @@@ucrC97 -p @otu_picking_params_97.txt -r \$QIIME/../gg_otus-13_5-release/rep_set/97_otus.fasta
#./awe.pl normalize_by_copy_number.py -i @ucrC97/otu_table.biom -o @@normalized_otus.biom


#print join(',',@ARGV)."\n";







#exit(0);







############################################
# upload trojan horse
#my $trojan_nodeid = shock_upload($shock, data => AWE::JOB::get_trojanhorse(\@output_directories, $resulttarfile));


############################################
#upload input files to SHOCK
#
#my $first_task = {};
#
#foreach my $input_file (@input_files_local) {
#	print "uploading input_file $input_file to SHOCK...\n";
#	my $inputfile_nodeid = shock_upload($shock, file => $input_file);
#	
#	#push(@temporary_shocknodes, $inputfile_nodeid);
#
#	$first_task->{'inputs'}->{basename($input_file)} = {
#		'host' => $shockurl,
#		'node' => $inputfile_nodeid
#	};
#}
#
#
#
#if (@output_files > 0) {
#	foreach my $output_file (@output_files) {
#		$first_task->{'outputs'}->{basename($output_file)} = {
#			'host' => $shockurl
#		};
#	}
#}
#
#
#if (@output_directories > 0) {
#
#	$first_task->{'outputs'}->{$resulttarfile} = {
#		#	'nonzero' => "1",
#		'host' => $shockurl
#	};
#}
#
#
#
#
#############################################
## create AWE job description
#
#
#
#
#
#
#############################################
## upload job to AWE
#
#print "submit job to AWE server...\n";
#
#my $response_content_hash = $awe->submit_job(json_data => $awe_qiime_job_json);
##print $json->pretty->encode( $response_content_hash )."\n";
#my $job_id =$response_content_hash->{data}->{id};
#
#
#unless (defined $job_id) {
#	print $json->pretty->encode( $response_content_hash )."\n";
#	print STDERR "error: jobid not defined\n";
#	exit(1);
#	
#}
#
#
#############################################
## wait for job completion
#
#
#print "AWE job submitted, job_id: $job_id\n";
#
#
#exit(0);
#
#my $jobstatus_hash = wait_for_job($awe, $job_id);
#

