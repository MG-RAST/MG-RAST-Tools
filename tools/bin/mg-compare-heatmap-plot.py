#!/usr/bin/env python

import os
import sys
import json
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-compare-heatmap-plot

VERSION
    %s

SYNOPSIS
    mg-compare-heatmap-plot [ --help, --input <input file or stdin>, --format <cv: 'text' or 'biom'>, --plot <filename for png>, --rlib <R lib path>, --height <image height in inches> --width <image width in inches> --dpi <image DPI> --order <boolean>, --label <boolean> ]

DESCRIPTION
    Tool to generate heatmap-dendrogram vizualizations from metagenome abundance profiles.
"""

posthelp = """
Input
    Tab-delimited table of abundance profiles, metagenomes in columns and annotation in rows.
    OR
    BIOM format of abundance profiles.

Output
    PNG file of heatmap-dendrogram.

EXAMPLES
    mg-compare-taxa --ids 'mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3' --level class --source RefSeq --format text | mg-compare-heatmap-plot --input - --format text --plot my_heatmap --height 5 --width 4 --dpi 200 --label

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
    parser.add_option("", "--format", dest="format", default='text', help="input format: 'text' for tabbed table, 'biom' for BIOM format, default is text")
    parser.add_option("", "--plot", dest="plot", default=None, help="filename for output plot")
    parser.add_option("", "--rlib", dest="rlib", default=None, help="R lib path")
    parser.add_option("", "--height", dest="height", type="float", default=5, help="image height in inches, default is 5")
    parser.add_option("", "--width", dest="width", type="float", default=4, help="image width in inches, default is 4")
    parser.add_option("", "--dpi", dest="dpi", type="int", default=300, help="image DPI, default is 300")
    parser.add_option("", "--order", dest="order", action="store_true", default=False, help="order columns, default is off")
    parser.add_option("", "--label", dest="label", action="store_true", default=False, help="label image rows, default is off")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if (opts.input != '-') and (not os.path.isfile(opts.input)):
        sys.stderr.write("ERROR: input data missing\n")
        return 1
    if opts.format not in ['text', 'biom']:
        sys.stderr.write("ERROR: invalid input format\n")
        return 1
    if not opts.plot:
        sys.stderr.write("ERROR: missing output filename\n")
        return 1
    if (not opts.rlib) and ('KB_PERL_PATH' in os.environ):
        opts.rlib = os.environ['KB_PERL_PATH']
    if not opts.rlib:
        sys.stderr.write("ERROR: missing path to R libs\n")
        return 1
    
    # parse input for R
    tmp_in  = 'tmp_'+random_str()+'.txt'
    tmp_hdl = open(tmp_in, 'w')
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        if opts.format == 'biom':
            try:
                indata = json.loads(indata)
                biom_to_tab(indata, tmp_hdl)
            except:
                sys.stderr.write("ERROR: input BIOM data not correct format\n")
                return 1
        else:
            tmp_hdl.write(indata)
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1
    tmp_hdl.close()
    
    # build R cmd
    order = 'TRUE' if opts.order else 'FALSE'
    label = 'TRUE' if opts.label else 'FALSE'
    r_cmd = """source("%s/plot_mg_heatdend.r")
suppressMessages( plot_mg_heatdend(
    table_in="%s",
    image_out="%s",
    order_columns=%s,
    label_rows=%s,
    image_height_in=%.1f,
    image_width_in=%.1f,
    image_res_dpi=%d
))"""%(opts.rlib, tmp_in, opts.plot, order, label, opts.height, opts.width, opts.dpi)
    execute_r(r_cmd)
    
    # cleanup
    os.remove(tmp_in)
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
