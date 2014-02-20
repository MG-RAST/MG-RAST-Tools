#!/usr/bin/env perl

use strict;
use warnings;

use FindBin;
use lib $FindBin::Bin;

use AWE::Client;
use AWE::Job;
use SHOCK::Client;

use USAGEPOD qw(parse_options);


my $aweserverurl =  $ENV{'AWE_SERVER_URL'};
my $shockurl =  $ENV{'SHOCK_SERVER_URL'};
my $clientgroup = $ENV{'AWE_CLIENT_GROUP'};

my $shocktoken=$ENV{'GLOBUSONLINE'} || $ENV{'KB_AUTH_TOKEN'};




my ($h, $help_text) = &parse_options (
	'name' => 'mg-amethst -- wrapper for amethst',
	'version' => '1',
	'synopsis' => 'mg-amethst -i <input> -o <output>',
	'examples' => 'ls',
	'authors' => 'Wolfgang Gerlach',
	'options' => [
		[ 'cmdfile|c=s',  "command file" ],
		[ 'output|o=s', "out" ],
		[ 'nowait|n',   "asynchronous call" ],
		[ 'help|h', "", { hidden => 1  }]
	]
);



if ($h->{'help'} || keys(%$h)==0) {
	print $help_text;
	exit(0);
}

#$h->{'input'} || die "no input defined";
#$h->{'output'} || die "no output defined";

$h->{'cmdfile'} || die "no cmdfile defined";

open FILE, $h->{'cmdfile'} or die $!;
while (my $line = <FILE>) {
	
	if ($line =~ /^\#job/) {
		my $cmd1 =  <FILE>;
		my $cmd2 =  <FILE>;
		my $sum_cmd =  <FILE>;
	
		print $cmd1."\n";
		print $cmd2."\n";
		print $sum_cmd."\n";
	}
	
}


close(FILE);


exit(0);

############################################
# connect to AWE server and check the clients

my $awe = new AWE::Client($aweserverurl, $shocktoken);
unless (defined $awe) {
	die;
}

$awe->checkClientGroup($clientgroup)==0 || die;


############################################
#connect to SHOCK server

print "connect to SHOCK\n";
my $shock = new SHOCK::Client($shockurl, $shocktoken); # shock production
unless (defined $shock) {
	die;
}

##############

#parse command file


##############
	
my $cmd = "AMETHST.pl -f test_commands \@".$h->{'input'}." -o \@\@".$h->{'output'};
	
my $job_id = AWE::Job::generateAndSubmitSimpleAWEJob('cmd' => $cmd, 'awe' => $awe, 'shock' => $shock, 'clientgroup' => $clientgroup);

print "job submitted: $job_id\n";

unless (defined($h->{'nowait'})) {
	AWE::Job::wait_and_download_job_results ('awe' => $awe, 'shock' => $shock, 'jobs' => [$job_id], 'clientgroup' => $clientgroup);
}

