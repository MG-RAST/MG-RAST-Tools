#!/usr/bin/env perl

use strict;
use warnings;

use awe;
use shock;

my $shockurl = "http://shock1.chicago.kbase.us:80";
#my $shockurl = 'http://shock.metagenomics.anl.gov';

my $aweserverurl = "http://140.221.84.148:8000"; # Wei's server
my $clientgroup = 'qiime-wolfgang';

my $shocktoken=$ENV{'GLOBUSONLINE'} || $ENV{'KB_AUTH_TOKEN'};


unless (@ARGV) {
	print "usage: mg-picrust-predict [file ...]\n";
	print "input is QIIME OTU file in BIOM format\n";
	print "data should have normalized with mg-picrust-normalize-16s-copy\n";
	exit(0);
}



############################################
# connect to AWE server and check the clients

my $awe = new AWE($aweserverurl, $shocktoken);
unless (defined $awe) {
	die;
}

$awe->checkClientGroup($clientgroup)==0 || die;


############################################
#connect to SHOCK server

print "connect to SHOCK\n";
my $shock = new Shock($shockurl, $shocktoken); # shock production
unless (defined $shock) {
	die;
}


my @jobs=();

foreach my $file (@ARGV) {
	
	#print $file."\n";
	
		
	
	my $cmd = "predict_metagenomes.py -i \@$file -o \@\@$file.metagenome_predictions.biom";
	
	my $job_id = AWE::Job::generateAndSubmitSimpleAWEJob('cmd' => $cmd, 'awe' => $awe, 'shock' => $shock);
	
	push (@jobs,$job_id);
	
	#print $cmd."\n";
	
	
}

print "all jobs submitted\n";
print "jobs: ".join(',', @jobs)."\n";



AWE::Job::wait_and_get_job_results ('awe' => $awe, 'shock' => $shock, 'jobs' => \@jobs, 'clientgroup' => $clientgroup);


