#!/usr/bin/env python

import os
import sys
import json
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-compare-pcoa-plot

VERSION
    %s

SYNOPSIS
    mg-compare-pcoa-plot [ --help, --input <input file or stdin>, --format <cv: 'text' or 'biom'>, --plot <filename for png>, --metadata <metadata field>, --color_group <json string or filepath>, --color_pos <integer>, --color_auto <boolean>, --rlib <R lib path>, --height <image height in inches>, --width <image width in inches>, --dpi <image DPI>, --three <boolean>, --label <boolean> ]

DESCRIPTION
    Tool to generate PCoA vizualizations from metagenome abundance profiles.
"""

posthelp = """
Input
    Tab-delimited table of abundance profiles, metagenomes in columns and annotation in rows.
    OR
    BIOM format of abundance profiles.

Output
    PNG file of PCoA.

EXAMPLES
    mg-compare-taxa --ids 'mgm4441619.3,mgm4441656.4,mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3' --level class --source RefSeq --format biom | mg-compare-pcoa-plot --input - --format biom --plot my_pcoa --metadata feature --height 5 --width 4 --dpi 200 --three --label

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
    parser.add_option("", "--metadata", dest="metadata", default=None, help="metadata field to color by, only for 'biom' input")
    parser.add_option("", "--color_group", dest="color_group", default=None, help="list of color groups in JSON or tabbed format - either as input string or filename")
    parser.add_option("", "--color_pos", dest="color_pos", type="int", default=1, help="position of color group to use, default is 1 (first)")
    parser.add_option("", "--color_auto", dest="color_auto", action="store_true", default=False, help="auto-create colors based on like group names, default is use group name as color")
    parser.add_option("", "--rlib", dest="rlib", default=None, help="R lib path")
    parser.add_option("", "--height", dest="height", type="float", default=6, help="image height in inches, default is 6")
    parser.add_option("", "--width", dest="width", type="float", default=6, help="image width in inches, default is 6")
    parser.add_option("", "--dpi", dest="dpi", type="int", default=300, help="image DPI, default is 300")
    parser.add_option("", "--three", dest="three", action="store_true", default=False, help="create 3-D PCoA, default is 2-D")
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
    if opts.metadata:
        opts.color_pos = 1
        opts.color_auto = True
    
    # parse input for R
    tmp_in  = 'tmp_'+random_str()+'.txt'
    tmp_hdl = open(tmp_in, 'w')
    mg_list = []
    gcolors = []
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        if opts.format == 'biom':
            try:
                indata = json.loads(indata)
                biom_to_tab(indata, tmp_hdl)
                # get mg list and metadata value list
                if opts.metadata:
                    for c in indata['columns']:
                        mg_list.append(c['id'])
                        value = 'null'
                        for v in c['metadata'].itervalues():
                            if ('data' in v) and (opts.metadata in v['data']):
                                value = v['data'][opts.metadata]
                        gcolors.append([value])
                else:
                    mg_list = map(lambda x: x['id'], indata['columns'])
            except:
                sys.stderr.write("ERROR: input BIOM data not correct format\n")
                return 1
        else:
            tmp_hdl.write(indata)
            mg_list = indata.split('\n')[0].strip().split('\t')
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1
    tmp_hdl.close()
    
    # get color groups if not in BIOM metadata and option used
    if (not gcolors) and opts.color_group:
        # is it json ?
        try:
            cdata = json.load(open(opts.color_group, 'r')) if os.path.isfile(opts.color_group) else json.loads(opts.color_group)
            for mg in mg_list:
                c_set = []
                for cd in cdata:
                    found_c = None
                    for c in cd.iterkeys():
                        if mg in cd[c]:
                            found_c = c
                            break
                    if found_c:
                        c_set.append(found_c)
                    else:
                        sys.stderr.write("ERROR: metagenome %s not in a group\n"%mg)
                        return 1
                gcolors.append(c_set)                    
        # no - its tabbed
        except:
            ctext = open(opts.color_group, 'r').read() if os.path.isfile(opts.color_group) else opts.color_group
            cdata = {}
            for line in ctext.strip().split("\n")[1:]:
                parts = line.strip().split("\t")
                cdata[parts[0]] = parts[1:]
            for mg in mg_list:
                if mg in cdata:
                    gcolors.append( cdata[mg] )
                else:
                    sys.stderr.write("ERROR: metagenome %s not in a group\n"%mg)
                    return 1

    # print color groups to file for R input
    tmp_clr = None
    if gcolors:
        tmp_clr = 'tmp_'+random_str()+'.txt'
        clr_hdl = open(tmp_clr, 'w')
        for i in range(len(gcolors[0])):
            clr_hdl.write("\t%d"%i)
        clr_hdl.write("\n")
        for i, mg in enumerate(mg_list):
            clr_hdl.write( "%s\t%s\n"%(mg, "\t".join(gcolors[i])) )
        clr_hdl.close()
    
    # build R cmd
    three = 'c(1,2,3)' if opts.three else 'c(1,2)'
    label = 'TRUE' if opts.label else 'FALSE'
    table = '"%s"'%tmp_clr if tmp_clr else 'NA'
    color = 'TRUE' if opts.color_auto else 'FALSE'
    r_cmd = """source("%s/plot_mg_pcoa.r")
suppressMessages( plot_mg_pcoa(
    table_in="%s",
    image_out="%s",
    plot_pcs=%s,
    label_points=%s,
    color_table=%s,
    color_column=%d,
    auto_colors=%s,
    image_height_in=%.1f,
    image_width_in=%.1f,
    image_res_dpi=%d
))"""%(opts.rlib, tmp_in, opts.plot, three, label, table, opts.color_pos, color, opts.height, opts.width, opts.dpi)
    execute_r(r_cmd)
    
    # cleanup
    os.remove(tmp_in)
    if tmp_clr:
        os.remove(tmp_clr)
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
