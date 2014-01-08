#!/usr/bin/env perl

use strict;
use warnings;
use File::Basename;

use shock;
use awe;

use JSON;

use Data::Dumper;
my $shockurl = "http://shock1.chicago.kbase.us:80";
#my $shockurl = 'http://shock.metagenomics.anl.gov';

my $aweserverurl = "http://140.221.84.148:8000"; # Wei's server
my $clientgroup = 'qiime-wolfgang';
my $shocktoken=$ENV{'GLOBUSONLINE'} || $ENV{'KB_AUTH_TOKEN'};


my @awe_job_states = ('in-progress', 'completed', 'queued', 'pending', 'deleted' , 'suspend' );






unless (@ARGV) {
	print "usage: mg-pick-OTUs [file ...]\n";
	print "input are 16S sequences in FASTA format\n";
	exit(0);
}






my $task_tmpls;

my $task_tmpls_json = <<EOF;
{
	"pick_closed_reference_otus" : {
		"cmd" : "pick_closed_reference_otus.py -i @[INPUT] -o ucr -p @[INPUT-PARAMETER] -r /home/ubuntu/data/gg_13_5_otus/rep_set/97_otus.fasta",
		"inputs" : ["[INPUT]", "[INPUT-PARAMETER]"],
		"outputs" : ["otu_table.biom"],
		"trojan" : {"out_files" : ["ucr/otu_table.biom"]}
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

my @jobs=();
#my $jobs_to_download = {};

foreach my $file (@ARGV) {
	print $file."\n";

	my $fasta = $file;
	if ($file =~ /\.gz$/) {
		system("gzip -d $file");
		$fasta = basename($file, ".gz");
	}
	
	unless (-e $fasta) {
		die "fasta file $fasta not found\n";
	}
	
	my $base = basename($fasta, ".fas", ".fna");
	
	$tasks->[1]->{'OUTPUT'} = $base.".otus.biom";
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
	
	my $job_id = $submission_result->{'data'}->{'id'};
	
	unless (defined($job_id)) {
		die "no job_id found";
	}
	
	push(@jobs, $job_id);
	
	
	print "result from AWE server:\n".$json->pretty->encode( $submission_result )."\n";
	
	
	
	
}

system("rm -f ./otu_picking_params_97.txt");


print "all jobs submitted... waiting for results\n";
print "job IDs: ".join(',', @jobs)."\n";
if (@jobs ==0 ) {
	die "no jobs submitted?";
}

AWE::Job::wait_and_get_job_results ('awe' => $awe, 'shock' => $shock, 'jobs' => \@jobs, 'clientgroup' => $clientgroup);



