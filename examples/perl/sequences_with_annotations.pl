#!/usr/bin/env perl
use JSON;
use LWP::UserAgent;
use URI::Escape;

# This script retrieves the table of sequence id, sequence, and annotation from the MG-RAST API and
# dumps what it gets

# get a user agent
my $ua = LWP::UserAgent->new;
$ua->agent("MyClient/0.1 ");

my $key = $ENV{"MGRKEY"};
# define the parameters
my $metagenome = $ARGV[0] ; 
my $annotation_type = "feature";
my $source = "SEED";
my $e_value = "15";
my $group_level = "family" ;
my $filter = "" ;

die "Metagenome ID argument is required!   
Usage:    sequences_with_annotations.pl <mgr accession number>   
Example:  sequences_with_annotations.pl mgm4440442.5\n "  unless $#ARGV + 1 == 1;
die "Don't recognize format of $metagenome" unless $metagenome =~ m/\d\d\d\d\d\d\d.\d/;

my $response;
my $content;
my $filename;
# retrieve the data
my $base_url = "http://api.metagenomics.anl.gov/1/annotation/sequence/$metagenome?"; 
my $url = $base_url."&auth=$key"."&type=$annotation_type&source=$source&evalue=$e_value";
print STDERR "Retrieving $url\n";
	
$response = $ua->get($url);  # , ":content_file" =>  STDERR );
	# check http header 
$content = $response->content;
die "Error with HTTP request:  ". $response->status_line."\n".$content unless $response->is_success ;
print STDOUT $content;
