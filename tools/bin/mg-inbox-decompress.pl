#!/usr/bin/env perl 

# this script detects the compression type and performs the extraction

use strict;
use warnings;
no warnings('once');

use Getopt::Long;
use File::Copy;
use File::Basename;
use POSIX qw(strftime);
use Cwd;
umask 000;

my $revision = "0";
my $run_dir = getcwd();

# options
my $file = "";

my $options = GetOptions ("input=s" => \$file);

unless (-s $file) {
    print  "Error: input file: [$file] does not exist or is size zero\n";
    print_usage();
    exit __LINE__;
}

print "input_file=$file\n";

my $type = "";
my $basename = $file;
if ($basename =~ s/^(.*)\.(tar\.gz|tgz)$/$1/) {
  $type = 'tar gzip';
} elsif ($basename =~ s/^(.*)\.zip$/$1/) {
  $type = 'zip';
} elsif ($basename =~ s/^(.*)\.(tar\.bz2|tbz|tbz2|tb2)$/$1/) {
  $type = 'tar bzip2';
} elsif ($basename =~ s/^(.*)\.gz$/$1/) {
  $type = 'gzip';
} elsif ($basename =~ s/^(.*)\.bz2$/$1/) {
  $type = 'bzip2';
}

my $command = "";
if ($type eq 'tar gzip') {
  $command = "tar -xzf '$file' &> $file.error_log";
} elsif ($type eq 'zip') {
  $command = "unzip -q -o '$file' &> $file.error_log";
} elsif ($type eq 'tar bzip2') {
  $command = "tar -xjf '$file' &> $file.error_log";
} elsif ($type eq 'gzip') {
  $command = "gunzip -d '$file' &> $file.error_log";
} elsif ($type eq 'bzip2') {
  $command = "bunzip2 -d '$file' &> $file.error_log";
}

system($command) == 0 or exit __LINE__;

print "Finished decompress on file $input\n";

exit(0);

sub print_usage{
    print "USAGE: mg-inbox-decompress.pl -input=<input file>\n";
}
