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

my $response;
my $content;
my $file_suffix = '.fastq.gz';
my $filename;
# retrieve the data
foreach my $file_id ('050.1', '050.2') {
	my $base_url = "http://api.metagenomics.anl.gov/1/download/$metagenome?file=".$file_id;
	my $url = $base_url."&auth=$key";
	print STDERR "Retrieving $url\n";
	
	if ($file_id eq '050.2') {
		$file_suffix = '.fasta.gz';
	}
	$filename = "$metagenome".$file_suffix;
	$response = $ua->get($url, ":content_file" =>  $filename);
	# check http header 
	$content = $response->content;
	if ($response->is_success) {
		last;
	}
}
die "Error with HTTP request:  ". $response->status_line."\n".$content unless $response->is_success ;
print STDERR "Writing \"$filename\"\n";
