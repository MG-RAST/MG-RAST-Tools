#!/usr/bin/env python

import os
import sys
import json
from argparse import ArgumentParser
from mglib import AUTH_LIST, VERSION, get_auth_token, random_str, biom_to_tab, execute_r

prehelp = """
NAME
    mg-compare-boxplot-plot

VERSION
    %s

SYNOPSIS
    mg-compare-boxplot-plot [ --help, --input <input file or stdin>, --format <cv: 'text' or 'biom'>, --plot <filename for png>, --reference <boolean>, --rlib <R lib path>, --height <image height in inches>, --width <image width in inches>, --dpi <image DPI>, --name <boolean>, --label <boolean> ]

DESCRIPTION
    Tool to generate boxplot vizualizations from metagenome abundance profiles.
"""

posthelp = """
Input
    Tab-delimited table of abundance profiles, metagenomes in columns and annotation in rows.
    OR
    BIOM format of abundance profiles.

Output
    PNG file of boxplot.

EXAMPLES
    mg-compare-taxa --ids 'mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3' --level class --source RefSeq --format text | mg-compare-boxplot-plot --input - --format text --plot my_heatmap --height 4 --width 5 --dpi 200 --label

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_argument("--user", dest="user", default=None, help="OAuth username")
    parser.add_argument("--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_argument("--token", dest="token", default=None, help="OAuth token")
    parser.add_argument("--input", dest="input", default='-', help="input: filename or stdin (-), default is stdin")
    parser.add_argument("--format", dest="format", default='biom', help="input format: 'text' for tabbed table, 'biom' for BIOM format, default is biom")
    parser.add_argument("--plot", dest="plot", default=None, help="filename for output plot")
    parser.add_argument("--rlib", dest="rlib", default=None, help="R lib path")
    parser.add_argument("--height", dest="height", type=float, default=8.5, help="image height in inches, default is 4")
    parser.add_argument("--width", dest="width", type=float, default=11, help="image width in inches, default is 5")
    parser.add_argument("--dpi", dest="dpi", type=int, default=300, help="image DPI, default is 300")
    parser.add_argument("--name", dest="name", type=int, default=0, help="label columns by name, default is by id: 1=true, 0=false")
    parser.add_argument("--label", dest="label", type=int, default=0, help="label image rows, default is off: 1=true, 0=false")
    
    # get inputs
    opts = parser.parse_args()
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
    for o in ['reference', 'name', 'label']:
        if getattr(opts, o) not in [0, 1]:
            sys.stderr.write("ERROR: invalid value for '%s'\n"%o)
            return 1
    
    return 0
    # get auth
    token = get_auth_token(opts)
    
    # parse input for R
    tmp_in  = 'tmp_'+random_str()+'.txt'
    tmp_hdl = open(tmp_in, 'w')
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        if opts.format == 'biom':
            try:
                indata = json.loads(indata)
                col_name = True if opts.name == 1 else False
                biom_to_tab(indata, tmp_hdl, col_name=col_name)
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
    label = 'TRUE' if opts.label == 1 else 'FALSE'
    r_cmd = """source("%s/plot_mg_boxplot.r")
suppressMessages( plot_mg_boxplot(
    table_in="%s",
    image_out="%s",
    label_rows=%s,
    image_height_in=%.1f,
    image_width_in=%.1f,
    image_res_dpi=%d
))"""%(opts.rlib, tmp_in, opts.plot, label, opts.height, opts.width, opts.dpi)
    execute_r(r_cmd)
    
    # cleanup
    os.remove(tmp_in)
    
    return 0
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))
