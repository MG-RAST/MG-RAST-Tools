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




sub process_pair {
	my ($cmd1, $cmd2, $sum_cmd) = @_;

	my ($matrix_file) = $cmd1 =~ /-f\s+(\S+)/;
	unless (defined $matrix_file) {
		die;
	}
	print "matrix_file: $matrix_file\n";

	my ($group_file) = $cmd1 =~ /-g\s+(\S+)/;
	unless (defined $group_file) {
		die;
	}
	print "group_file: $group_file\n";
	
	my ($tree_file) = $cmd1 =~ /-a\s+(\S+)/;
	if (defined $tree_file) {
		print "tree_file: $tree_file\n";
	}
	
	
	if (-e $matrix_file) {
		print "found $matrix_file\n";
	} else {
		die "$matrix_file not found"
	}
	
	if (-e $group_file) {
		print "found $group_file\n";
	} else {
		die "$group_file not found"
	}
	
	if (defined $tree_file) {
		
		if (-e $tree_file) {
			print "found $tree_file\n";
		} else {
			die "$tree_file not found"
		}
	}
	
	
}



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
		chomp($cmd1);
		chomp($cmd2);
		chomp($sum_cmd);
	
		print $cmd1."\n";
		print $cmd2."\n";
		print $sum_cmd."\n";
	
		process_pair($cmd1, $cmd2, $sum_cmd);
	
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

