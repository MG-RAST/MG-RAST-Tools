#!/usr/bin/env perl

use strict;
use warnings;
use File::Basename;
use Pod::Usage;

use shock;
use awe;

use JSON;
use Getopt::Long::Descriptive;

use USAGEPOD qw(parse_options);

use Data::Dumper;



# export AWE_SERVER_URL="http://140.221.85.36:8000" or "http://140.221.84.148:8000"
# export SHOCK_SERVER_URL="http://shock1.chicago.kbase.us:80"
# export AWE_CLIENT_GROUP=qiime-wolfgang



my $aweserverurl =  $ENV{'AWE_SERVER_URL'};
my $shockurl =  $ENV{'SHOCK_SERVER_URL'};
my $clientgroup = $ENV{'AWE_CLIENT_GROUP'};

my $shocktoken=$ENV{'GLOBUSONLINE'} || $ENV{'KB_AUTH_TOKEN'};



my ($h, $help_text) = &parse_options (
	'name' => 'mg-pick-OTUs -- wrapper for picrust-normalize',
	'version' => '1',
	'synopsis' => 'mg-pick-OTUs -i <input> -o <output>',
	'examples' => 'ls',
	'authors' => 'Wolfgang Gerlach',
	'options' => [
		[ 'input|i=s',  "16S sequences in FASTA format" ],
		[ 'output|o=s', "QIIME OTUs in BIOM format" ],
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




my $task_tmpls;

my $task_tmpls_json = <<EOF;
{
	"pick_closed_reference_otus" : {
		"cmd" : "pick_closed_reference_otus.py -i @[INPUT] -o ucr -p @[INPUT-PARAMETER] -r /home/ubuntu/data/gg_13_5_otus/rep_set/97_otus.fasta",
		"inputs" : ["[INPUT]", "[INPUT-PARAMETER]"],
		"outputs" : ["ucr/otu_table.biom"]
	}
}
EOF



$task_tmpls = decode_json($task_tmpls_json);





my $tasks_json = <<EOF;
[
{
	"task_id" : "0_pick_closed_reference_otus",
	"task_template" : "pick_closed_reference_otus",
	"INPUT" : ["shock", "[INPUT]", "input.fas"],
	"INPUT-PARAMETER" : ["shock", "[INPUT-PARAMETER]", "otu_picking_params_97.txt"],
	"TROJAN" : ["shock", "[TROJAN1]", "trojan.pl"]
},
{
	"task_id" : "1_rename",
	"task_cmd" : "mv @[INPUT] @@[OUTPUT]",
	"INPUT" : ["task", "0_pick_closed_reference_otus", "otu_table.biom"],
	"OUTPUT" : "XXXXXXXXXX",
	"TROJAN" : ["shock", "[TROJAN2]", "trojan2.pl"]
}
]
EOF


my $tasks = decode_json($tasks_json);


sub create_qiime_pipeline {
	





	
	# create AWE job (without input data !)
	my $awe_qiime_job = AWE::Job->new(
	'info' => {
		"pipeline"=> "qiime-wolfgang",
		"name"=> "qiime-job_".int(rand(100000)),
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
	print "AWE job without input:\n".$json->pretty->encode( $awe_qiime_job->hash() )."\n";
	
	return $awe_qiime_job;
	
}





my $awe = new AWE($aweserverurl, $shocktoken);
unless (defined $awe) {
	die;
}

$awe->checkClientGroup($clientgroup) == 0 or exit(1);


print "connect to SHOCK\n";
my $shock = new Shock($shockurl, $shocktoken);
unless (defined $shock) {
	die;
}

my $json = JSON->new;



#create parameter file
system("echo \"pick_otus:enable_rev_strand_match True\npick_otus:similarity 0.97\" > ./otu_picking_params_97.txt");

#my @jobs=();
#my $jobs_to_download = {};

#foreach my $file (@ARGV) {

if (-e $h->{'output'}) {
	die "error: outputfile \"".$h->{'output'}."\" already exists.";
}


my $file = $h->{'input'};
print $file."\n";

my $fasta = $file;
if ($file =~ /\.gz$/) {
	system("gzip -d $file") == 0 or die;
	$fasta = basename($file, ".gz");
}

unless (-e $fasta) {
	die "fasta file $fasta not found\n";
}

#my $base = basename($fasta, ".fas", ".fna");

$tasks->[1]->{'OUTPUT'} = $h->{'output'};
my $awe_qiime_job = create_qiime_pipeline();



#print Dumper($awe_qiime_job->{'tasks'});
#exit(0);



#define job input
my $job_input = {};
$job_input->{'INPUT'}->{'file'} = $fasta;   	  # local file to be uploaded
$job_input->{'INPUT-PARAMETER'}->{'file'} = './otu_picking_params_97.txt';   	  # local file to be uploaded
$job_input->{'TROJAN1'}->{'data'} = AWE::Job::get_trojanhorse(%{$task_tmpls->{'pick_closed_reference_otus'}->{'trojan'}});
$job_input->{'TROJAN2'}->{'data'} = AWE::Job::get_trojanhorse();
$job_input->{'TROJAN3'}->{'data'} = AWE::Job::get_trojanhorse();

#upload job input files
$shock->upload_temporary_files($job_input);


# create job with the input defined above
my $workflow = $awe_qiime_job->create(%$job_input);

#overwrite jobname:
#$workflow->{'info'}->{'name'} = $sample;

print "AWE job ready for submission:\n".$json->pretty->encode( $workflow )."\n";

print "submit job to AWE server...\n";
my $submission_result = $awe->submit_job('json_data' => $json->encode($workflow));

my $job_id = $submission_result->{'data'}->{'id'} || die "no job_id found";


print "result from AWE server:\n".$json->pretty->encode( $submission_result )."\n";


system("rm -f ./otu_picking_params_97.txt");

print "job submitted: $job_id\n";

unless (defined($h->{'nowait'})) {
	AWE::Job::wait_and_download_job_results ('awe' => $awe, 'shock' => $shock, 'jobs' => [$job_id], 'clientgroup' => $clientgroup);
}


