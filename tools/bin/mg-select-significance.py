#!/usr/bin/env python

import os
import sys
import json
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-select-significance

VERSION
    %s

SYNOPSIS
    mg-select-significance [ --help, --input <input file or stdin>, --format <cv: 'text' or 'biom'>, --output <cv: 'text' or 'biom'>, --order <integer>, --direction <cv: 'asc', 'desc'>, --cols <integer>, --rows <integer> ]

DESCRIPTION
    Tool to order and subselect grouped metagenomic abundace profiles with significance statistics.
"""

posthelp = """
Input
    Tab-delimited table of abundance profiles with significance statistics

Output
    Altered tab-delimited table based on input and options.

EXAMPLES
    mg-compare-taxa --ids 'mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3' --level class --source RefSeq --format text | mg-group-significance --input - --format text --groups '{"group1":["mgm4441679.3","mgm4441680.3"],"group2":["mgm4441681.3","mgm4441682.3"]}' --stat_test Kruskal-Wallis | mg-select-significance --input - --cols 4 --rows 10

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
    parser.add_option("", "--format", dest="format", default='biom', help="input format: 'text' for tabbed table, 'biom' for BIOM format, default is biom")
    parser.add_option("", "--output", dest="output", default='biom', help="output format: 'text' for tabbed table, 'biom' for BIOM format, default is biom")
    parser.add_option("", "--order", dest="order", default=None, help="column number to order output by (0 for last column), default is no ordering")
    parser.add_option("", "--direction", dest="direction", default="desc", help="direction of order. 'asc' for ascending order, 'desc' for descending order, default is desc")
    parser.add_option("", "--cols", dest="cols", default=None, help="number of columns from the left to return from input table, default is all")
    parser.add_option("", "--rows", dest="rows", default=None, help="number of rows from the top to return from input table, default is all")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if (opts.input != '-') and (not os.path.isfile(opts.input)):
        sys.stderr.write("ERROR: input data missing\n")
        return 1
    if opts.format not in ['text', 'biom']:
        sys.stderr.write("ERROR: invalid input format\n")
        return 1
    if opts.output not in ['text', 'biom']:
        sys.stderr.write("ERROR: invalid output format\n")
        return 1
    if opts.direction not in ['asc', 'desc']:
        sys.stderr.write("ERROR: invalid order direction\n")
        return 1
    
    # parse inputs
    biom = None
    rows = []
    cols = []
    data = []    
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        if opts.format == 'biom':
            try:
                biom = json.loads(indata)
                rows, cols, data = biom_to_matrix(biom, sig_stats=True)
            except:
                sys.stderr.write("ERROR: input BIOM data not correct format\n")
                return 1
        else:
            rows, cols, data = tab_to_matrix(indata)
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1
    
    # first we sort
    if opts.order is not None:
        rev_order = True if opts.direction == 'desc' else False
        order_col = opt2int('order', opts.order)
        if order_col > len(cols):
            sys.stderr.write("ERROR: --order value is greater than number of columns in table\n")
        order_col  = order_col - 1
        rd_merged  = zip(rows, data)
        rd_sorted  = sorted(rd_merged, key=lambda x: x[1][order_col], reverse=rev_order)
        rows, data = zip(*rd_sorted)
        
    # subselect rows
    if opts.rows is not None:
        subrow = opt2int('rows', opts.rows)
        rows = rows[:subrow]
        data = data[:subrow]
    if opts.cols is not None:
        subcol = opt2int('cols', opts.cols)
        cols = cols[:subcol]
        data = sub_matrix(data, subcol)
    
    # output data
    if biom and (opts.output == 'biom'):
        # get list of new rows and columns with old indexes
        br_ids = [r['id'] for r in biom['rows']]
        bc_ids = [c['id'] for c in biom['columns']]
        rindex = []
        cindex = []
        for r in rows:
            try:
                rindex.append( br_ids.index(r) )
            except:
                pass
        for c in cols:
            try:
                cindex.append( bc_ids.index(c) )
            except:
                pass
        # update biom
        biom['id'] = biom['id']+'_altered'
        biom['data'] = []
        biom['rows'] = [biom['rows'][r] for r in rindex]
        biom['columns'] = [biom['columns'][c] for c in cindex]
        biom['matrix_type'] = 'dense'
        for r in rindex:
            new_row = []
            for c in cindex:
                new_row.append(data[r][c])
            biom['data'].append(new_row)
        safe_print(json.dumps(biom)+'\n')
    else:
        safe_print( "\t%s\n" %"\t".join(cols) )
        for i, d in enumerate(data):
            safe_print( "%s\t%s\n" %(rows[i], "\t".join(map(str, d))) )
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
