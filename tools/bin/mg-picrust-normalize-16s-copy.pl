#!/usr/bin/env perl

use strict;
use warnings;

use awe;
use shock;


use USAGEPOD qw(parse_options);


my $aweserverurl =  $ENV{'AWE_SERVER_URL'};
my $shockurl =  $ENV{'SHOCK_SERVER_URL'};
my $clientgroup = $ENV{'AWE_CLIENT_GROUP'};

my $shocktoken=$ENV{'GLOBUSONLINE'} || $ENV{'KB_AUTH_TOKEN'};




my ($h, $help_text) = &parse_options (
	'name' => 'mg-picrust-normalize-16s-copy -- wrapper for picrust-normalize',
	'version' => '1',
	'synopsis' => 'mg-picrust-normalize-16s-copy -i <input> -o <output>',
	'examples' => 'ls',
	'authors' => 'Wolfgang Gerlach',
	'options' => [
		[ 'input|i=s',  "QIIME OTU file in BIOM format" ],
		[ 'output|o=s', "QIIME OTU file in BIOM format (normalized by 16S copy number)" ],
		[ 'nowait|n',   "asynchronous call" ],
		[ 'help|h', "", { hidden => 1  }]
	]
);



if ($h->{'help'} || keys(%$h)==0) {
	print $help_text;
	exit(0);
}

$h->{'input'} || die "no input defined";
$h->{'output'} || die "no output defined";



############################################
# connect to AWE server and check the clients
my $awe = new AWE($aweserverurl, $shocktoken);
unless (defined $awe) {
	die;
}
$awe->checkClientGroup($clientgroup)==0 || die;


############################################
#connect to SHOCK server
my $shock = new Shock($shockurl, $shocktoken); # shock production
unless (defined $shock) {
	die;
}



my $cmd = "normalize_by_copy_number.py -i \@".$h->{'input'}." -o \@\@".$h->{'output'};


my $job_id = AWE::Job::generateAndSubmitSimpleAWEJob('cmd' => $cmd, 'awe' => $awe, 'shock' => $shock, 'clientgroup' => $clientgroup);
	
print "job submitted: $job_id\n";
print "get results using:\n";
print "mg-awe-submit.pl --wait_and_get_jobs=$job_id\n";

unless (defined($h->{'nowait'})) {
	AWE::Job::wait_and_download_job_results ('awe' => $awe, 'shock' => $shock, 'jobs' => [$job_id], 'clientgroup' => $clientgroup);
}
