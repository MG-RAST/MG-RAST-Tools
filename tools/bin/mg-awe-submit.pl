#!/usr/bin/env perl

use strict;
use warnings;



#https://github.com/MG-RAST/Shock/blob/master/libs/shock.pm
use shock;
use awe;

use JSON;

use Data::Dumper;
use File::Basename;

use USAGEPOD qw(parse_options);


my $aweserverurl =  $ENV{'AWE_SERVER_URL'};
my $shockurl =  $ENV{'SHOCK_SERVER_URL'};
my $clientgroup = $ENV{'AWE_CLIENT_GROUP'};


my $shocktoken=$ENV{'GLOBUSONLINE'} || $ENV{'KB_AUTH_TOKEN'};

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


sub getJobStates {
	
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
	$states->{$_}=[] for @awe_job_states;
	foreach my $job (@{$jobs->{data}}){
		
		my $job_id = $job->{id};
		my $state = lc($job->{state});
		
		push(@{ $states->{$state} } , $job_id);
		
		
		
	}
	return $states;
}


sub showAWEstatus {
	
	
	
	my $states = getJobStates();
	
	print "\n\n** job states **\n";
	#print "$_: ".($states->{$_}||'0')."\n" for @awe_job_states;
	
	foreach my $state (@awe_job_states) {
		if (@{$states->{$state}} > 0) {
			print $state.': '.join(',', @{$states->{$state}})."\n";
		}
	}
	
	
	print "\n\n** job states summary **\n";
	foreach my $state (@awe_job_states) {
		
		print $state.': '.@{$states->{$state}}."\n";
		
	}
	
	if (keys($states) > 6) { # in case Wei introduces new states.. ;-)
		die;
	}
	
}






########################################################################################
########################################################################################
########################################################################################
########################################################################################
# START





my ($h, $help_text) = &parse_options (
	'name' => 'mg-awe-submit',
	'version' => '1',
	'synopsis' => 'mg-awe-submit --status',
	'examples' => 'ls',
	'authors' => 'Wolfgang Gerlach',
	'options' => [
		'',
		'Actions:',
		[ 'status'						, "show job states on AWE server"],
		[ 'cmd=s'						, "command to execute"],
		[ 'show_jobs=s'					, " "],
		[ 'check_jobs=s'				, " "],
		[ 'download_jobs=s'				, "download specified jobs if state==completed"],
		[ 'wait_and_download_jobs=s'	, "wait for completion and download specified jobs"],
		[ 'delete_jobs=s'				, "deletes jobs and temporary shock nodes, unless keep_nodes used"],
		[ 'shock_clean'					, "delete all temporary nodes from SHOCK server"],
		[ 'shock_query=s'				, "query SHOCK node"],
		[ 'shock_view=s'                , "view SHOCK node"],
		'',
		'Options:',
		[ 'keep_nodes'					, "use with --delete_jobs"],
		[ 'wait_completed'				, "wait until any job is in state completed"],
		[ 'output_files=s'				, "specify extra output files for --cmd"],
		[ 'clientgroup=s',				, "clientgroup"],
		[ 'help|h'						, "", { hidden => 1  }]
	]
);



if ($h->{'help'} || keys(%$h)==0) {
	print $help_text;
	exit(0);
}


if (defined($h->{'clientgroup'})) {
	$clientgroup = $h->{'clientgroup'};
}


if (defined($h->{"status"})) {
	showAWEstatus();
	exit(0);
} elsif (defined($h->{"wait_completed"})) {
	
	my $completed = 0;
	while (1) {
		my $states = getJobStates();
		$completed = @{$states->{'completed'}};
		if ($completed > 0) {
			last;
		}
		sleep(5);
	}
	
	print "$completed job(s) are in state \"complete\"\n";
	exit(0);
} elsif (defined($h->{"wait_and_download_jobs"})) {
	
	my @jobs = split(',', $h->{"wait_and_download_jobs"});
	
	############################################
	# connect to AWE server and check the clients
	
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	
	$awe->checkClientGroup($clientgroup) == 0 or exit(1);
	
	############################################
	#connect to SHOCK server
	
	print "connect to SHOCK\n";
	my $shock = new Shock($shockurl, $shocktoken); # shock production
	unless (defined $shock) {
		die;
	}
	
	AWE::Job::wait_and_download_job_results ('awe' => $awe, 'shock' => $shock, 'jobs' => \@jobs, 'clientgroup' => $clientgroup);
	
	exit(0);

} elsif (defined($h->{"delete_jobs"})) {
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	my @jobs = split(',', $h->{"delete_jobs"});
	
	if (defined($h->{"keep_nodes"})) { # delete jobs without deleteing shock nodes
		foreach my $job (@jobs) {
			my $dd = $awe->deleteJob($job);
			print Dumper($dd);
		}
	} else {
		
		print "connect to SHOCK\n";
		my $shock = new Shock($shockurl, $shocktoken); # shock production
		unless (defined $shock) {
			die;
		}
		
		
		AWE::Job::delete_jobs ('awe' => $awe, 'shock' => $shock, 'jobs' => \@jobs, 'clientgroup' => $clientgroup);
		
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

} elsif (defined($h->{"shock_view"})) {
	
	
	my @nodes = split(',', $h->{"shock_view"});
	
	my $shock = new Shock($shockurl, $shocktoken);
	unless (defined $shock) {
		die;
	}
	
	foreach my $node (@nodes) {
		my $response =  $shock->get('node/'.$node);
		print Dumper($response);
	}
	
	
	
	exit(0);
	
} elsif (defined($h->{"shock_clean"})) {
	
	my $shock = new Shock($shockurl, $shocktoken);
	unless (defined $shock) {
		die;
	}
		
	my $response =  $shock->query('temporary' => 1);
	
	#my $response =  $shock->query('statistics.length_max' => 1175);
	print Dumper($response);
	#exit(0);
	
	my @list =();
	
	unless (defined $response->{'data'}) {
		die;
	}
	
	foreach my $node (@{$response->{'data'}}) {
		#print $node->{'id'}."\n";
		push(@list, $node->{'id'});
	}
	
	print "found ".@list. " nodes that can be deleted\n";
	
	foreach my $node (@list) {
		my $ret = $shock->delete_node($node);
		defined($ret) or die;
		print Dumper($ret);
	}
	
	
	exit(0);

} elsif (defined($h->{"download_jobs"})) {
	
	my @jobs = split(/,/,$h->{"download_jobs"});
	
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	my $shock = new Shock($shockurl, $shocktoken); # shock production
	unless (defined $shock) {
		die;
	}
	
	my $use_download_dir = 1;
	my $only_last_task = 0;
	
	AWE::Job::download_jobs('awe' => $awe, 'shock' => $shock, 'jobs' => \@jobs, 'clientgroup' => $clientgroup, 'use_download_dir' => $use_download_dir, 'only_last_task' => $only_last_task);
	
	print "done.\n";
	exit(0);
	
} elsif (defined($h->{"check_jobs"})) {
		
	my @jobs = split(/,/,$h->{"check_jobs"});
	
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	my $ret = AWE::Job::check_jobs('awe' => $awe,  'jobs' => \@jobs, 'clientgroup' => $clientgroup);
	
	if ($ret ==0) {
		print "all jobs completed :-) \n";
		exit(0);
	}

	print "jobs not completed :-( \n";
	exit(1);
} elsif (defined($h->{"show_jobs"})) {
	
	my @jobs = split(/,/,$h->{"show_jobs"});
	
	my $awe = new AWE($aweserverurl, $shocktoken);
	unless (defined $awe) {
		die;
	}
	
	foreach my $job (@jobs) {
		my $job_obj = $awe->getJobStatus($job);
		print Dumper($job_obj);
	}
	
	#my $ret = AWE::Job::check_jobs('awe' => $awe,  'jobs' => \@jobs, 'clientgroup' => $clientgroup);
	
	#if ($ret ==0) {
	#	print "all jobs completed :-) \n";
	#	exit(0);
	#}
	
	#print "jobs not completed :-( \n";
	#exit(1);
	exit(0);
	
} elsif (defined($h->{"get_all"})) {
	#getAWE_results_and_cleanup();
	
	
	
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
	
	$awe->checkClientGroup($clientgroup) == 0 or exit(1);
	
	
	############################################
	#connect to SHOCK server
	
	print "connect to SHOCK\n";
	my $shock = new Shock($shockurl, $shocktoken); # shock production
	unless (defined $shock) {
		die;
	}

	
	## compose AWE job ##
	AWE::Job::generateAndSubmitSimpleAWEJob('cmd' => $cmd, 'awe' => $awe, 'shock' => $shock, 'clientgroup' => $clientgroup, @moreopts);
	
	
	
	exit(0);

}




