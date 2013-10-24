#!/usr/bin/env perl
use JSON;
use LWP::UserAgent;
use URI::Escape;
use Data::Dumper;

# get a user agent
my $ua = LWP::UserAgent->new;
$ua->agent("abundance_matrix.pl ");

# define the parameters
my $metagenomes = ["mgm4447102.3","mgm4447943.3"];
my $group_level = "family"; # "family"; "species";
my $result_type = "abundance";
my $source = "SEED";

# retrieve the data
my $base_url = "http://api.metagenomics.anl.gov/1/matrix/organism";
my $url = $base_url.uri_escape("?group_level=$group_level&result_type=$result_type&source=$source&evalue=8&".join("&", map{"id=".$_}@$metagenomes));
 
print STDERR "Retrieving $url\n";
my $response = $ua->get($url);
die "Error with HTTP request:  ". $response->status_line."\n".$content unless $response->is_success ;
my $content = $response->content;

# create a perl data structure from the returned JSON
my $json = new JSON;

my $biom = $json->decode( $content );

#print Dumper($abundances)."\n";

$data = [[]];
for (my $m=0; $m <= $#{$abundances->{rows}}; $m++)
        {
        for (my $n=0; $n < $#{$abundances->{columns}}; $n++)
        {
        $data->[$m][$n] = 0;
        }
        }
map{ $data->[$_->[0]][$_->[1]] = $_->[2] }  @{$biom->{data}};

print "Annotation\t" . join("\t", map( $_->{id} , @{$biom->{columns}}))."\n";
for (my $r=0; $r<scalar(@{$biom->{rows}}); $r++) {
         {  
                print @{$biom->{rows}}[$r]->{"id"} ."\t"; 
                print join("\t", @{$data->[$r]}); 
                # @{$biom->{columns}}."\n";
        }
       print "\n";
}

