#!/usr/bin/env python

import os
import sys
import json
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-group-significance

VERSION
    %s

SYNOPSIS
    mg-group-significance [ --help, --input <input file or stdin>, --format <cv: 'text' or 'biom'>, --output <cv: 'text' or 'biom'>, --metadata <metadata field>, --groups <json string or filepath>, --group_pos <integer>, --plot <filename for pdf>, --rlib <R lib path>, --stat_test <cv: Kruskal-Wallis, t-test-paired, Wilcoxon-paired, t-test-unpaired, Mann-Whitney-unpaired-Wilcoxon, ANOVA-one-way>, --order <column number>, --direction <cv: 'asc', 'desc'>, --height <image height in inches>, --width <image width in inches>, --dpi <image DPI> ]

DESCRIPTION
    Tool to apply matR-based statistical tests to grouped metagenomic abundace profiles.
"""

posthelp = """
Input
    1. Tab-delimited table of abundance profiles, metagenomes in columns and annotation in rows.
       OR
       BIOM format of abundance profiles.
    2. Groups in JSON format - either as input string or filename

Output
    Tab-delimited table of input abundance profiles with significance statistics based on input groups.

EXAMPLES
    mg-compare-taxa --ids 'mgm4441619.3,mgm4441656.4,mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3' --level class --source RefSeq --format biom | mg-group-significance --input - --format biom --metadata latitude --stat_test Kruskal-Wallis --direction asc

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
    parser.add_option("", "--format", dest="format", default='biom', help="input format: 'text' for tabbed table, 'biom' for BIOM format, default is biom")
    parser.add_option("", "--output", dest="output", default='biom', help="output format: 'text' for tabbed table, 'biom' for BIOM format, default is biom")
    parser.add_option("", "--plot", dest="plot", default=None, help="filename for output plot, optional")
    parser.add_option("", "--stat_test", dest="stat_test", default='Kruskal-Wallis', help="supported statistical tests, one of: Kruskal-Wallis, t-test-paired, Wilcoxon-paired, t-test-unpaired, Mann-Whitney-unpaired-Wilcoxon, ANOVA-one-way, default is Kruskal-Wallis")
    parser.add_option("", "--metadata", dest="metadata", default=None, help="metadata field to group by, only for 'biom' input")
    parser.add_option("", "--groups", dest="groups", default=None, help="list of groups in JSON or tabbed format - either as input string or filename")
    parser.add_option("", "--group_pos", dest="group_pos", type="int", default=1, help="position of group to use, default is 1 (first)")
    parser.add_option("", "--rlib", dest="rlib", default=None, help="R lib path")
    parser.add_option("", "--order", dest="order", default=None, help="column number to order output by, default is last column")
    parser.add_option("", "--direction", dest="direction", default="desc", help="direction of order. 'asc' for ascending order, 'desc' for descending order, default is desc")
    parser.add_option("", "--height", dest="height", type="float", default=6, help="image height in inches, default is 6")
    parser.add_option("", "--width", dest="width", type="float", default=6, help="image width in inches, default is 6")
    parser.add_option("", "--dpi", dest="dpi", type="int", default=300, help="image DPI, default is 300")
    
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
    if (not opts.rlib) and ('KB_PERL_PATH' in os.environ):
        opts.rlib = os.environ['KB_PERL_PATH']
    if not opts.rlib:
        sys.stderr.write("ERROR: missing path to R libs\n")
        return 1
    if opts.direction not in ['asc', 'desc']:
        sys.stderr.write("ERROR: invalid order direction\n")
        return 1
    
    # parse inputs
    tmp_in  = 'tmp_'+random_str()+'.txt'
    tmp_out = 'tmp_'+random_str()+'.txt'
    tmp_hdl = open(tmp_in, 'w')
    mg_list = []
    groups  = []
    biom = None
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        if opts.format == 'biom':
            try:
                biom = json.loads(indata)
                mg_list = map(lambda x: x['id'], biom['columns'])
                biom_to_tab(biom, tmp_hdl)
                if opts.metadata:
                    groups = metadata_from_biom(biom, opts.metadata)
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
                for g, mgs in gdata[opts.group_pos-1].items():
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
    
    # validate groups
    if len(groups) != len(mg_list):
        sys.stderr.write("ERROR: Not all metagenomes in a group\n")
        return 1
    
    # build R cmd
    fig_out    = '"%s"'%opts.plot if opts.plot else 'NULL'
    order_by   = 'NULL' if opts.order is None else int(opts.order)
    order_desc = 'TRUE' if opts.direction == 'desc' else 'FALSE'
    group_str  = 'c('+','.join(map(lambda x: '"%s"'%x, groups))+')'
    r_cmd = """source("%s/group_stats_plot.r")
suppressMessages( group_stats_plot(
    file_in="%s",
    file_out="%s",
    figure_out=%s,
    figure_width_in=%.1f,
    figure_height_in=%.1f,
    figure_res_dpi=%d,
    stat_test="%s",
    order_by=%s,
    order_decreasing=%s,
    my_grouping=%s
))"""%(opts.rlib, tmp_in, tmp_out, fig_out, opts.height, opts.width, opts.dpi, opts.stat_test, order_by, order_desc, group_str)
    execute_r(r_cmd)
    
    # output results
    results = open(tmp_out, 'r').read()
    os.remove(tmp_in)
    os.remove(tmp_out)
    
    if biom and (opts.output == 'biom'):
        cnum = biom['shape'][1]
        rids = [r['id'] for r in biom['rows']]
        rrows, rcols, rdata = tab_to_matrix(results)
        if (len(rrows) != biom['shape'][0]) or (len(rcols[:cnum]) != biom['shape'][1]):
            sys.stderr.write("ERROR: significance test returned invalid results\n")
            return 1
        # add stats to row data, re-order
        new_rows = []
        new_data = []
        for i, row in enumerate(rdata):
            # get row
            rindex = rids.index(rrows[i])
            robj = biom['rows'][rindex]
            if not robj['metadata']:
                robj['metadata'] = {'significance': []}
            else:
                robj['metadata']['significance'] = []
            # add stats
            for j, stat in enumerate(row[cnum:]):
                try:
                    stat = float(stat)
                except:
                    stat = None
                robj['metadata']['significance'].append((rcols[cnum:][j], stat))
            new_rows.append(robj)
            new_data.append(row[:cnum])
        # update biom
        biom['id'] = biom['id']+'_sig'
        biom['rows'] = new_rows
        biom['data'] = new_data
        biom['matrix_type'] = 'dense'
        for i, g in enumerate(groups):
            biom['columns'][i]['group'] = g
        safe_print(json.dumps(biom)+'\n')
    else:
        safe_print(results)
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
