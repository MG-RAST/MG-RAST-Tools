#!/usr/bin/env perl
use JSON;
use LWP::UserAgent;
use URI::Escape;
use Data::Dumper;

# get a user agent
my $ua = LWP::UserAgent->new;
$ua->agent("MyClient/0.1 ");


# set the parameters
my $key = $ENV{"MGRKEY"};
my $metagenome = $ARGV[0];
my $source = $ARGV[1];

die "Metagenome ID and source arguments are required!
Usage: species_abundance_biom.pl <mgr accession number> <source>
Example: species_abundance_biom.pl mgm4440026.3 GenBank\n " unless $#ARGV + 1 == 2;
die "Don't recognize format of $metagenome" unless $metagenome =~ m/\d\d\d\d\d\d\d.\d/;


# retrieve the data
my $base_url = "http://api.mg-rast.org/1/matrix/organism";
my $url=$base_url.uri_escape((defined($key)?"?auth=$key&":"?")."id=$metagenome&source=$source");
#print "url: $url\n";
my $content = $ua->get($url)->content;


#pretty-print BIOM output
my $json = new JSON;
my $biom = $json->pretty->encode( $json->decode( $content ) );
print $biom."\n";

#creates hash and prints to terminal:
#print Dumper($json->decode( $content ))."\n";
