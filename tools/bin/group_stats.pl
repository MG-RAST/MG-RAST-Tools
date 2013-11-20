#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Long;

# Default for variables
my $lib_path  = $ENV{'R_LIBS'} || "";
my $file_in   = "";
my $file_out  = "";
my $stat_test = "Kruskal-Wallis";
my $order_by  = "NULL";
my $order_decreasing   = "TRUE";
my $group_lines_count  = 0;
my $group_line_process = 0;
my $grouping = "";
my $help     = 0;
my $verbose  = 0;

if ( ! GetOptions (
		   "l|lib_path=s"           => \$lib_path,
		   "i|file_in=s"            => \$file_in,
		   "o|file_out=s"           => \$file_out,
		   "t|stat_test=s"          => \$stat_test,
		   "b|order_by=s"           => \$order_by,
           "d|order_decreasing=s"   => \$order_decreasing,
		   "c|group_lines_count=s"  => \$group_lines_count, 
		   "p|group_line_process=s" => \$group_line_process,
		   "g|grouping=s"           => \$grouping,
		   "h|help!"                => \$help,
		   "v|verbose!"             => \$verbose
		  )
   ) { &usage(); }
if ((@ARGV > 0) && ($ARGV[0] =~ /-h/)) { &usage(); }
unless ($file_in && $file_out) { &usage("missing file_in or file_out"); }

# create and run R command that will be executed to perform the analysis
$grouping = $grouping ? qq(c($grouping)) : "NA";
my $r_cmd = qq(source("$script_path/group_stats.r")
suppressMessages( group_stats(
    file_in="$file_in",
    file_out="$file_out",
    stat_test="$stat_test",
    order_by=$order_by,
    order_decreasing=$order_decreasing,
    group_lines=$group_lines_count,
    group_line_to_process=$group_line_process,
    my_grouping=$grouping
))
);
system(qq(echo "$r_cmd" | R --vanilla --slave --silent));

sub usage {
  my ($err) = @_;
  my $script_call = join('\t', @_);
  my $num_args = scalar @_;
  print STDOUT ($err ? "ERROR: $err" : '') . qq(
script: $0

USAGE:
# general usage
group_stats.pl [options]

# normal usage, with groupings taken from file_in (using first, and only, line of groupings)
group_stats.pl -i sample_time_series_data.groups_in_file.txt -o my_output.txt -c 1 -p 1

# normal usage, with groupings assigned by properly formatted R string
group_stats.pl -i sample_time_series_data.groups_in_file.txt -o my_output.txt -c 1 -p 0 -g "1,1,1,2,2,2,3,3,3"

DESCRIPTION:
Tool to apply matR-based statistical tests.
Designated test is applied with groupings defined in the input file or an input argument.
order_by NULL will order data by the calculated false discovery rate.
Use an integer value for -b|order_by to order the data by any other column in the output data file.

OPTIONS:
    -l|lib_path             (string)          location of group_stats.r        default: $lib_path
    -i|file_in              (string)          input data file                  default: $file_in
    -o|file_out             (string)          output results file              default: $file_out
    -t|stat_test            (string)          matR statisitical tests          default: $stat_test
    -b|order_by             (NULL or int)     column to order data             default: $order_by
    -d|order_decreasing     (TRUE or FALSE)   order by decreasing              default: $order_decreasing
    -c|group_lines_count    (int)             number of lines with groupings   default: $group_lines_count
    -p|group_line_process   (int)             line of groupings to use         default: $group_line_process
    -g|grouping             (string)          R formatted grouping string      default: $grouping
________________________________________________________________________________________
    -h|help                 (flag)            see the help/usage
    -v|verbose              (flag)            run in verbose mode

NOTES:
Supported statistical tests (-t|stat_test) include the following tests available in matR
    Kruskal-Wallis 
    t-test-paired 
    Wilcoxon-paired 
    t-test-unpaired 
    Mann-Whitney-unpaired-Wilcoxon 
    ANOVA-one-way

Groups can be entered in two ways, as a comma-seperated list list (e.g. '1,1,2,2' or '"grp1","grp1","grp2","grp2"')
with the -g|grouping option, or if grouping information is contained in the first n lines of the input, use the 
-c|group_lines_count and -p|group_line_process arguments to sepcify the number of lines that contain group information 
and the group line that should be used respectively.

);
  exit $err ? 1 : 0;
}
