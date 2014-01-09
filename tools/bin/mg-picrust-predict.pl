#!/usr/bin/env perl

use strict;
use warnings;

use awe;
use shock;

use Getopt::Long::Descriptive;

my $shockurl = "http://shock1.chicago.kbase.us:80";
#my $shockurl = 'http://shock.metagenomics.anl.gov';

my $aweserverurl = "http://140.221.84.148:8000"; # Wei's server
my $clientgroup = 'qiime-wolfgang';

my $shocktoken=$ENV{'GLOBUSONLINE'} || $ENV{'KB_AUTH_TOKEN'};

my $help_text = <<EOF;

NAME
    mg-picrust-predict -- something

VERSION
    1

SYNOPSIS
    mg-picrust-predict -i <input> -o <output>

DESCRIPTION
    Some description...

    Parameters:
XXX-XXX
    Output:

    Some output...

EXAMPLES
    ls

SEE ALSO
    -

AUTHORS
    Wolfgang Gerlach

EOF

my ($h, $usage) = describe_options(
'',
[ 'input|i=s', "QIIME OTU file in BIOM format"],
[ 'output|o=s',   "PICRUST functional prediction in BIOM format" ],
[],
[ 'help|h', "", { hidden => 1  }]
);

my $htext = $usage->text;
$help_text =~ s/XXX-XXX/$htext/;

if ($h->help) {
	print $help_text;
	exit(0);
}

$h->input || die "no input defined";
$h->output || die "no output defined";



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


	
my $cmd = "predict_metagenomes.py -i \@".$h->{'input'}." -o \@\@".$h->{'output'};
	
my $job_id = AWE::Job::generateAndSubmitSimpleAWEJob('cmd' => $cmd, 'awe' => $awe, 'shock' => $shock);

print "job submitted: $job_id\n";

#AWE::Job::wait_and_get_job_results ('awe' => $awe, 'shock' => $shock, 'jobs' => \@jobs, 'clientgroup' => $clientgroup);


