#!/usr/bin/env python

import os
import sys
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-correlate-metadata-fdr

VERSION
    %s

SYNOPSIS
    mg-correlate-metadata-fdr [ --help, --input <input file or stdin>, --rlib <R lib path>, --p_value_pos <integer> ]

DESCRIPTION
    Calculate FDR (False Discovery Rate) for given annotations correlated by a metadata value
"""

posthelp = """
Input
    BIOM format of abundance profiles with metadata.

Output
    Tabbed table of annotation and correlation p-value.

EXAMPLES
    mg-compare-taxa --ids 'mgm4441619.3,mgm4441656.4,mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3' --level class --source RefSeq --format biom | mg-correlate-metadata --input - --metadata latitude | mg-correlate-metadata-fdr --input - 

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--input", dest="input", default='-', help="input: filename or stdin (-), default is stdin")
    parser.add_option("", "--rlib", dest="rlib", default=None, help="R lib path")
    parser.add_option("", "--p_value_pos", dest="p_value_pos", default=None, help="column number of p-values, default is last column")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if (opts.input != '-') and (not os.path.isfile(opts.input)):
        sys.stderr.write("ERROR: input data missing\n")
        return 1
    if (not opts.rlib) and ('KB_PERL_PATH' in os.environ):
        opts.rlib = os.environ['KB_PERL_PATH']
    if not opts.rlib:
        sys.stderr.write("ERROR: missing path to R libs\n")
        return 1
    
    # parse inputs
    tmp_in  = 'tmp_'+random_str()+'.txt'
    tmp_out = 'tmp_'+random_str()+'.txt'
    tmp_hdl = open(tmp_in, 'w')
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        tmp_hdl.write(indata)
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1
    tmp_hdl.close()
    
    # build R cmd
    p_val = '"last"' if opts.p_value_pos is None else int(opts.p_value_pos)
    r_cmd = """source("%s/mg_calculate_fdr.r")
suppressMessages( mg_calculate_fdr(
    table_in="%s",
    table_out="%s",
    p_value_column=%s
))"""%(opts.rlib, tmp_in, tmp_out, p_val)
    execute_r(r_cmd)
    
    # output results
    results = open(tmp_out, 'r').read()
    os.remove(tmp_in)
    os.remove(tmp_out)
    safe_print(results)
    
    return 0
    
if __name__ == "__main__":
    sys.exit( main(sys.argv) )
    