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


##############################################

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
	
	return ($matrix_file, $group_file, $tree_file);
}

##################################################

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

print "Configuration:\n";
print "aweserverurl: ".($aweserverurl || 'undef') ."\n";
print "shockurl: ". ($shockurl || 'undef') ."\n";
print "clientgroup: ". ($clientgroup || 'undef') ."\n\n";

#$h->{'input'} || die "no input defined";
#$h->{'output'} || die "no output defined";

$h->{'cmdfile'} || die "no cmdfile defined";


my @tasks=();

open FILE, $h->{'cmdfile'} or die $!;
while (my $line = <FILE>) {
	
	if ($line =~ /^\#job/) {
		my $cmd1 =  <FILE>;
		my $cmd2 =  <FILE>;
		my $sum_cmd =  <FILE>;
		chomp($cmd1);
		chomp($cmd2);
		chomp($sum_cmd);
	
		my $pair_file = $line.$cmd1."\n".$cmd2."\n".$sum_cmd;
	
		#print $cmd1."\n";
		#print $cmd2."\n";
		#print $sum_cmd."\n";
	
		my @input_files = process_pair($cmd1, $cmd2, $sum_cmd);
		push(@tasks, [$pair_file, @input_files]);
		
	}
	
}


close(FILE);




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



my $task_tmpls;

my $task_tmpls_json = <<EOF;
{
	"amethst" : {
		"cmd" : "AMETHST.pl -f @[CMDFILE] -z",
		"inputs" : ["[CMDFILE]"],
		"outputs" : ["[OUTPUT]"]
	}
}
EOF

$task_tmpls = decode_json($task_tmpls_json);


#check if output file already exists
foreach my $task (@tasks) {
	my ($pair_file, $matrix_file, $group_file, $tree_file) = @{$task};
	
	my $output_file = $matrix_file.'.'.$group_file.'_results.zip';
	
	if (-e $output_file) {
		die "output file $output_file already exists\n";
	}
}

# create and sumbit workflows
for (my $i = 0 ; $i < @tasks ; ++i) {
	my $task = $tasks[$i];
	
	my ($pair_file, $matrix_file, $group_file, $tree_file) = @{$task};
	
	
	my $input_filename = basename($pair_file).'_'.$i.'.txt';
	
	print "got:\n $pair_file\n $matrix_file, $group_file, $tree_file\n";
	
	
	my $output_file = $matrix_file.'.'.$group_file.'_results.zip';
	
	my $tasks =
	[
	{
		"task_id" => "0_amethst",
		"task_template" => "amethst",
		"INPUT" => ["shock", "[INPUT]", $input_filename],
		"OUTPUT" => $output_file
	}
	];
	
	
	
	my $awe_job = AWE::Job->new(
	'info' => {
		"pipeline"=> "amethst",
		"name"=> "amethst-job_".int(rand(100000)),
		"project"=> "project",
		"user"=> "wgerlach",
		"clientgroups"=> $clientgroup,
		"noretry"=> JSON::true
	},
	'shockhost' => $shockurl,
	'task_templates' => $task_tmpls,
	'tasks' => $tasks
	);
	
	my $json = JSON->new;
	print "AWE job without input:\n".$json->pretty->encode( $awe_job->hash() )."\n";
	
	
	#define and upload job input files
	my $job_input = {};
	$job_input->{'INPUT'}->{'data'} = $pair_file;
	$shock->upload_temporary_files($job_input);

	
	
	# create job with the input defined above
	my $workflow = $awe_qiime_job->create(%$job_input, 'OUTPUT' => $h->{'output'});#define workflow output

	print "AWE job ready for submission:\n";
	print $json->pretty->encode( $workflow )."\n";
	
	exit(0);
	print "submit job to AWE server...\n";
	my $submission_result = $awe->submit_job('json_data' => $json->encode($workflow));
	
	my $job_id = $submission_result->{'data'}->{'id'} || die "no job_id found";
	
	
	print "result from AWE server:\n".$json->pretty->encode( $submission_result )."\n";
	
	print "job submitted: $job_id\n";
	
	unless (defined($h->{'nowait'})) {
		AWE::Job::wait_and_download_job_results ('awe' => $awe, 'shock' => $shock, 'jobs' => [$job_id], 'clientgroup' => $clientgroup);
	}
	
}

print "finished\n";"