#!/usr/bin/env perl
use JSON;
use LWP::UserAgent;
use URI::Escape;
use Data::Dumper;

# get a user agent
my $ua = LWP::UserAgent->new;
$ua->agent("MyClient/0.1 ");

# set the parameters
my $api_url = "http://dunkirk.mcs.anl.gov/~tharriso/mgrast/api.cgi";
my @ids= ('4447943.3', '4447192.3', '4447103.3', '4447102.3', '4447101.3', '4447971.3', '4447970.3', '4447903.3');
my $id_str = "id=mgm".join("&id=mgm", @ids);
my $source = "GenBank";
my $gene = "dnaA";

# retrieve the data
my $url = $api_url."/matrix/function?$id_str&source=$source&grep=$gene";
print "url: $url\n";
my $content = $ua->get($url)->content;

# create perl data structure from json
my $json = new JSON;
my $biom = $json->decode($content);
my $matrix = sparse2dense($biom->{data});

# print out abundance matrix
open(OUTFILE, ">dnaA.tab");
print OUTFILE "\t".join("\t", map {$_->{id}} @{$biom->{columns}})."\n";
for (my $r=0; $r<scalar(@{$biom->{rows}}); $r++) {
    print OUTFILE $biom->{rows}[$r]{id}."\t".join("\t", @{$matrix->[$r]})."\n";
}
close(OUTPUT);
print "dnaA.tab written\n";

sub sparse2dense {
    my ($data, $cmax, $rmax) = @_;

    my $dmatrix = [];
    foreach my $i (0..$rmax-1) {
        my $row = [];
        map { push @$row, 0 } (0..$cmax-1);
        push @$dmatrix, $row;
    }
    map { $dmatrix->[$_->[0]][$_->[1]] = $_->[2] } @$data;
    return $dmatrix;
}
