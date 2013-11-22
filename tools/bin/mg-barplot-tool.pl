#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Long;

# Default for variables
my $lib_path  = $ENV{'R_LIBS'} || "";
my $file_in   = "";
my $file_out  = "";
my $plot_out  = "";
my $stat_test = "Kruskal-Wallis";
my $order_by  = "NULL";
my $my_n = 5;
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
	   "z|plot_out=s"           => \$plot_out,
	   "t|stat_test=s"          => \$stat_test,
	   "b|order_by=s"           => \$order_by,
	   "n|my_n=i"               => \$my_n, 
       "d|order_decreasing=s"   => \$order_decreasing,
	   "c|group_lines_count=i"  => \$group_lines_count, 
	   "p|group_line_process=i" => \$group_line_process,
	   "g|grouping=s"           => \$grouping,
	   "h|help!"                => \$help,
	   "v|verbose!"             => \$verbose		   
	  )
   ) { &usage(); }
if ((@ARGV > 0) && ($ARGV[0] =~ /-h/)) { &usage(); }
unless ($file_in && $file_out) { &usage("missing file_in or file_out"); }

# create and run R command that will be executed to perform the analysis
$grouping = $grouping ? qq(c($grouping)) : "NA";
my $r_cmd = qq(source("$lib_path/barplot_tool.r")
suppressMessages( barplot_tool(
    file_in="$file_in",
    file_out="$file_out",
    figure_out="$plot_out",
    stat_test="$stat_test",
    order_by=$order_by,
    my_n=$my_n,
    order_decreasing=$order_decreasing,
    group_lines=$group_lines_count,
    group_line_to_process=$group_line_process,
    my_grouping=$grouping
))
);
system(qq(echo '$r_cmd' | R --vanilla --slave --silent));

sub usage {
  my ($err) = @_;
  print STDOUT ($err ? "ERROR: $err" : '') . qq(
script: $0

USAGE:
# general usage
barplot_tool.pl [options]

# normal usage, with groupings taken from file_in (using first line of groupings from two)
barplot_tool.pl -i sample_data2.groups_in_file.txt -o my_output.txt -c 2 -p 1 [other options]

# normal usage, with groupings assigned by properly formatted R string (groupings are in the file, but are skipped)
barplot_tool.pl -i sample_data2.groups_in_file.txt -o my_output.txt-c 2 -p 0 -g "1,1,1,2,2,2,3,3,3" [other options]

DESCRIPTION:
Tool to apply matR-based statistical tests.
Designated test is applied with groupings defined in the input file or an input argument.
order_by NULL will order data by the calculated false discovery rate.


OPTIONS:
    -l|lib_path             (string)          location of group_stats.r        default: $lib_path
    -i|file_in              (string)          input data file                  default: $file_in
    -o|file_out             (string)          output results file              default: $file_out
    -z|plot_out             (string)          name of output barplot figure    default: $plot_out
    -t|stat_test            (string)          matR statisitical tests          default: $stat_test
    -b|order_by             (NULL or int)     column to order data             default: $order_by
    -n|my_n                 (int)             number of categories to plot     default: $my_n
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
    my $status = $err ? 1 : 0;
    exit $status;
}
