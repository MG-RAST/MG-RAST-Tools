#!/usr/bin/env python

import os
import sys
import json
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-biom-view

VERSION
    %s

SYNOPSIS
    mg-biom-view [ --help, --input <input file or stdin>, --row_start <integer>, --row_end <integer>, --col_start <integer>, --col_end <integer>, --stats <boolean> ]

DESCRIPTION
    Tool to view slice of BIOM file as table with row and column ids
"""

posthelp = """
Input
    BIOM file

Output
    Tab-delimited table of BIOM sub-selection

EXAMPLES
    mg-biom-view --help

SEE ALSO
    -

AUTHORS
    %s
"""

def opt2int(opt, x):
    try:
        i = int(x)
    except:
        sys.stderr.write("ERROR: --%s must be an integer\n"%opt)
        sys.exit(1)
    return i

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--input", dest="input", default='-', help="input: filename or stdin (-), default is stdin")
    parser.add_option("", "--row_start", dest="row_start", default=None, help="row position to start table with, default is first")
    parser.add_option("", "--row_end", dest="row_end", default=None, help="row position to end table with, default is last")
    parser.add_option("", "--col_start", dest="col_start", default=None, help="column position to start table with, default is first")
    parser.add_option("", "--col_end", dest="col_end", default=None, help="column position to end table with, default is last")
    parser.add_option("", "--stats", dest="stats", action="store_true", default=False, help="include significance stats in output, default is off")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if (opts.input != '-') and (not os.path.isfile(opts.input)):
        sys.stderr.write("ERROR: input data missing\n")
        return 1
    
    # parse inputs
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        try:
            biom = json.loads(indata)
            rows, cols, data = biom_to_matrix(biom, sig_stats=opts.stats)
        except:
            sys.stderr.write("ERROR: input BIOM data not correct format\n")
            return 1
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1
    
    row_start = 0 if opts.row_start is None else opt2int('row_start', opts.row_start)-1
    row_end   = len(rows) if opts.row_end is None else opt2int('row_end', opts.row_end)
    col_start = 0 if opts.col_start is None else opt2int('col_start', opts.col_start)-1
    col_end   = len(cols) if opts.col_end is None else opt2int('col_end', opts.col_end)
    
    # output data
    try:
        sub_rows = rows[row_start:row_end]
        safe_print( "\t%s\n" %"\t".join(cols[col_start:col_end]) )
        for i, d in enumerate(data[row_start:row_end]):
            safe_print( "%s\t%s\n" %(sub_rows[i], "\t".join(map(str, d[col_start:col_end]))) )
    except:
        sys.stderr.write("ERROR: unable to sub-select BIOM, inputted positions are out of bounds\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit( main(sys.argv) )
