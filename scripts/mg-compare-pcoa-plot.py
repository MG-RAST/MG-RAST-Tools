#!/usr/bin/env python

import os
import sys
import json
from optparse import OptionParser
from mglib.mglib import *

prehelp = """
NAME
    mg-compare-pcoa-plot

VERSION
    %s

SYNOPSIS
    mg-compare-pcoa-plot [ --help, --input <input file or stdin>, --format <cv: 'text' or 'biom'>, --plot <filename for png>, --reference <boolean>, --distance <cv: bray-curtis, euclidean, maximum, manhattan, canberra, minkowski, difference>, --metadata <metadata field>, --groups <json string or filepath>, --group_pos <integer>, --color_auto <boolean>, --rlib <R lib path>, --height <image height in inches>, --width <image width in inches>, --dpi <image DPI>, --three <boolean>, --name <boolean>, --label <boolean> ]

DESCRIPTION
    Tool to generate PCoA vizualizations from metagenome abundance profiles.
"""

posthelp = """
Input
    1. Tab-delimited table of abundance profiles, metagenomes in columns and annotation in rows.
       OR
       BIOM format of abundance profiles.
    2. Groups in JSON format - either as input string or filename

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
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")
    parser.add_option("", "--input", dest="input", default='-', help="input: filename or stdin (-), default is stdin")
    parser.add_option("", "--format", dest="format", default='biom', help="input format: 'text' for tabbed table, 'biom' for BIOM format, default is biom")
    parser.add_option("", "--plot", dest="plot", default=None, help="filename for output plot")
    parser.add_option("", "--distance", dest="distance", default='bray-curtis', help="distance metric, one of: bray-curtis, euclidean, maximum, manhattan, canberra, minkowski, difference, default is bray-curtis")
    parser.add_option("", "--metadata", dest="metadata", default=None, help="metadata field to color by, only for 'biom' input")
    parser.add_option("", "--groups", dest="groups", default=None, help="list of groups in JSON or tabbed format - either as input string or filename")
    parser.add_option("", "--group_pos", dest="group_pos", type="int", default=1, help="position of group to use, default is 1 (first)")
    parser.add_option("", "--color_auto", dest="color_auto", type="int", default=0, help="auto-create colors based on like group names, default is use group name as color: 1=true, 0=false")
    parser.add_option("", "--rlib", dest="rlib", default=None, help="R lib path")
    parser.add_option("", "--height", dest="height", type="float", default=10, help="image height in inches, default is 6")
    parser.add_option("", "--width", dest="width", type="float", default=10, help="image width in inches, default is 6")
    parser.add_option("", "--dpi", dest="dpi", type="int", default=300, help="image DPI, default is 300")
    parser.add_option("", "--three", dest="three", type="int", default=0, help="create 3-D PCoA, default is 2-D: 1=true, 0=false")
    parser.add_option("", "--name", dest="name", type="int", default=0, help="label columns by name, default is by id: 1=true, 0=false")
    parser.add_option("", "--label", dest="label", type="int", default=0, help="label image rows, default is off: 1=true, 0=false")
    
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
        opts.color_auto = 1
    for o in ['reference', 'color_auto', 'three', 'name', 'label']:
        if getattr(opts, o) not in [0, 1]:
            sys.stderr.write("ERROR: invalid value for '%s'\n"%o)
            return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # parse inputs
    tmp_in  = 'tmp_'+random_str()+'.txt'
    tmp_hdl = open(tmp_in, 'w')
    mg_list = []
    groups  = []
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        if opts.format == 'biom':
            try:
                indata  = json.loads(indata)
                mg_list = map(lambda x: x['id'], indata['columns'])
                col_name = True if opts.name == 1 else False
                biom_to_tab(indata, tmp_hdl, col_name=col_name)
                if opts.metadata:
                    groups = metadata_from_biom(indata, opts.metadata)
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
    
    # get groups if not in BIOM metadata and option used
    if (len(groups) == 0) and opts.groups:
        # is it json ?
        ## example of 2 group sets in json format
        ## [ {"group1": ["mg_id_1", "mg_id_2"], "group2": ["mg_id_3", "mg_id_4", "mg_id_5"]},
        ##   {"group1": ["mg_id_1", "mg_id_2", "mg_id_3"], "group2": ["mg_id_4", "mg_id_5"]} ]
        try:
            gdata = json.load(open(opts.groups, 'r')) if os.path.isfile(opts.groups) else json.loads(opts.groups)
            if opts.group_pos > len(gdata):
                sys.stderr.write("ERROR: position (%d) of group is out of bounds\n"%opts.group_pos)
                return 1
            for m in mg_list:
                found_g = None
                for g, mgs in gdata[opts.group_pos-1].iteritems():
                    if m in mgs:
                        found_g = g
                        break
                if found_g:
                    groups.append(found_g)
                else:
                    sys.stderr.write("ERROR: metagenome %s not in a group\n"%m)
                    return 1                  
        # no - its tabbed
        except:
            gtext = open(opts.groups, 'r').read() if os.path.isfile(opts.groups) else opts.groups
            grows, gcols, gdata = tab_to_matrix(gtext)
            if opts.group_pos > len(gdata[0]):
                sys.stderr.write("ERROR: position (%d) of group is out of bounds\n"%opts.group_pos)
            for m in mg_list:
                try:
                    midx = gcols.index(m)
                    groups.append(gdata[midx][opts.group_pos-1])
                except:
                    sys.stderr.write("ERROR: metagenome %s not in a group\n"%m)
                    return 1
    
    # print groups to file for R input
    tmp_group = None
    if len(groups) == len(mg_list):
        tmp_group = 'tmp_'+random_str()+'.txt'
        hdl_group = open(tmp_group, 'w')
        hdl_group.write("\tgroup\n")
        for i, m in enumerate(mg_list):
            hdl_group.write("%s\t%s\n"%(m, ''.join([x if ord(x) < 128 else '?' for x in groups[i]])))
        hdl_group.close()
    elif len(groups) > 0:
        sys.stderr.write("Warning: Not all metagenomes in a group\n")
    
    # build R cmd
    three = 'c(1,2,3)' if opts.three == 1 else 'c(1,2)'
    label = 'TRUE' if opts.label == 1 else 'FALSE'
    table = '"%s"'%tmp_group if tmp_group else 'NA'
    color = 'TRUE' if opts.color_auto == 1 else 'FALSE'
    r_cmd = """source("%s/plot_mg_pcoa.r")
suppressMessages( plot_mg_pcoa(
    table_in="%s",
    image_out="%s",
    plot_pcs=%s,
    dist_metric="%s",
    label_points=%s,
    color_table=%s,
    color_column=1,
    auto_colors=%s,
    image_height_in=%.1f,
    image_width_in=%.1f,
    image_res_dpi=%d
))"""%(opts.rlib, tmp_in, opts.plot, three, opts.distance, label, table, color, opts.height, opts.width, opts.dpi)
    execute_r(r_cmd)
    
    # cleanup
    os.remove(tmp_in)
    if tmp_group:
        os.remove(tmp_group)
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
