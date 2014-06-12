package USAGEPOD;
use Exporter;
use Getopt::Long;

@ISA = ('Exporter');
@EXPORT = qw(parse_options);

sub parse_options {
	my %h = @_;
	
	my $arguments = {};
	
	
	my $help_name = $h{'name'} || '-';
	my $help_version = $h{'version'} || '-';
	my $help_synopsis = $h{'synopsis'} || '-';
	my $help_description = $h{'description'} || 'some description';
	
	my $help_output = $h{'output'} || 'some output';
	my $help_examples = $h{'examples'} || '-';
	my $help_authors = $h{'authors'} || '-';
	
	
	my $prefix = '    ';
	
	my $help_options = $h{'options'} || die "options not defined";
	
	
	# get longest option
	my $longest_opt = 0;
	foreach my $opt_array (@$help_options) {
		if (@$opt_array > 0) {
			my ($opt) = @$opt_array;
			if (length($opt) > $longest_opt) {
				$longest_opt = length($opt);
			}
		}
	}
	
	
	my @opt_list=();
	my $options_description="";
	foreach my $opt_array (@$help_options) {
		
		unless (ref($opt_array) eq 'ARRAY') {
			$options_description .= $prefix.$opt_array."\n";
			next;
		}
		if (@$opt_array > 0) {
			my ($opt, $opt_help, $prop) = @$opt_array;
			unless (defined $prop) {
				$prop={};
			}
			
			push(@opt_list, $opt);
			
			while (length($opt) < $longest_opt+1) {
				$opt.=' ';
			}
			unless ($prop->{'hidden'}) {
				$options_description .= $prefix.' --'.$opt." ".$opt_help."\n";
			}
			
		} else {
			$options_description .= "\n";
		}
	}
	
	
	GetOptions ($arguments, @opt_list);
	
	
	
	my $help_text = <<EOF;
	
NAME
    $help_name
	
VERSION
    $help_version
	
SYNOPSIS
    $help_synopsis
	
DESCRIPTION
    $help_description
	
    Parameters:
$options_description

    Output:
    $help_output
	
EXAMPLES
    $help_examples
	
SEE ALSO
    -
	
AUTHORS
    $help_authors
	
EOF
	
	
	return ($arguments, $help_text);
}



1;
