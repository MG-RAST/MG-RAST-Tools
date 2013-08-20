#!/usr/bin/env perl
use JSON;
use LWP::UserAgent;
use URI::Escape;
use Data::Dumper;

# get a user agent
my $ua = LWP::UserAgent->new;
$ua->agent("MyClient/0.1 ");

my $key = $ENV{"MGRKEY"};
# define the parameters
my $metagenome = $ARGV[0] ; 
my $group_level = "family" ;
my $result_type = "abundance";
my $source = "SEED";

die "Metagenome ID argument is required!   
Usage:    download_metagenome_sequences.pl <mgr accession number>   
Example:  download_metagenome_sequences.pl mgm4440442.5\n "  unless $#ARGV + 1 == 1;
die "Don't recognize format of $metagenome" unless $metagenome =~ m/\d\d\d\d\d\d\d.\d/;

# retrieve the data
my $base_url = "http://api.metagenomics.anl.gov/1/download/$metagenome?file=050.2";
my $url = $base_url."&auth=$key";
print STDERR "Retrieving $url\n"; 
my $response = $ua->get($url, ":content_file" => "$metagenome.gz" );
# check http header 
my $content = $response->content;
die "Error with HTTP request:  ". $response->status_line."\n".$content unless $response->is_success ;
print STDERR "Writing $metagenome.gz\n";
