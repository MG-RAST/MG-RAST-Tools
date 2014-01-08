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




sub getAWE_results_and_cleanup {
	
	my @completed_jobs = getCompletedJobs();
	
	
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	#print "connect to SHOCK\n";
	my $shock = new Shock($shockurl, $shocktoken); # shock production
	unless (defined $shock) {
		die;
	}

	
	my $job_deletion_ok =  AWE::Job::get_jobs_and_cleanup('awe' => $awe, 'shock' => $shock, 'jobs' => \@completed_jobs, 'clientgroup' => $clientgroup);
	
	
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
	
	return @jobs;
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
	print "      mg-awe-submit.pl --wait_completed\n";
	exit(0);
}


my $h = {};

GetOptions($h, 'cmd=s' , 'status', 'get_all', 'get_jobs=s' , 'delete=s' , 'shock_query=s' , 'shock_clean' , 'output_files=s', 'wait_completed');



if (defined($h->{"status"})) {
	showAWEstatus($ARGV[0]);
	exit(0);
} elsif (defined($h->{"wait_completed"})) {
	while (showAWEstatus('completed') > 0) {
		sleep(5);
	}
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
	
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	my $shock = new Shock($shockurl, $shocktoken); # shock production
	unless (defined $shock) {
		die;
	}
	
	AWE::Job::get_jobs_and_cleanup('awe' => $awe, 'shock' => $shock, 'jobs' => \@jobs, 'clientgroup' => $clientgroup);
	
	
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
	
	
	############################################
	# connect to AWE server and check the clients
	
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	checkClients($awe, $clientgroup) == 0 or exit(1);
	
	
	############################################
	#connect to SHOCK server
	
	print "connect to SHOCK\n";
	my $shock = new Shock($shockurl, $shocktoken); # shock production
	unless (defined $shock) {
		die;
	}

	
	## compose AWE job ##
	AWE::Job::generateAndSubmitSimpleAWEJob('cmd' => $cmd, 'awe' => $awe, 'shock' => $shock, @moreopts);
	
	
	
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

