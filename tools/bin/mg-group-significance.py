#!/usr/bin/env python

import os
import sys
import json
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-group-significance

VERSION
    %s

SYNOPSIS
    mg-group-significance [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --input <input file or stdin>, --format <cv: 'text' or 'biom'>, --groups <json string or filepath>, --plot <filename for pdf>, --rlib <R lib path>, --stat_test <cv: Kruskal-Wallis, t-test-paired, Wilcoxon-paired, t-test-unpaired, Mann-Whitney-unpaired-Wilcoxon, ANOVA-one-way>, --order <column number>, --direction <cv: 'asc', 'desc'> ]

DESCRIPTION
    Tool to apply matR-based statistical tests to grouped metagenomic abundace profiles.
"""

posthelp = """
Input
    1. Tab-delimited table of abundance profiles, metagenomes in columns and annotation in rows.
       OR
       BIOM format of abundance profiles.
    2. Groups in JSON format - either as input string or filename:
       ie. {"group1": ["mg_id_1", "mg_id_3"], "group2": ["mg_id_2", "mg_id_4"], "group3": ["mg_id_5", "mg_id_6", "mg_id_7"]}

Output
    Tab-delimited table of input abundance profiles with significance statistics based on input groups.

EXAMPLES
    mg-compare-taxa --ids 'mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3' --level class --source RefSeq --format text | mg-group-significance --input - --format text --groups '{"group1":["mgm4441679.3","mgm4441680.3"],"group2":["mgm4441681.3","mgm4441682.3"]}' --stat_test Kruskal-Wallis --direction asc

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
    parser.add_option("", "--format", dest="format", default='text', help="input format: 'text' for tabbed table, 'biom' for BIOM format, default is text")
    parser.add_option("", "--groups", dest="groups", default=None, help="groups in JSON format - either as input string or filename")
    parser.add_option("", "--plot", dest="plot", default=None, help="filename for output plot, optional")
    parser.add_option("", "--rlib", dest="rlib", default=None, help="R lib path")
    parser.add_option("", "--stat_test", dest="stat_test", default='Kruskal-Wallis', help="supported statistical tests, one of: Kruskal-Wallis, t-test-paired, Wilcoxon-paired, t-test-unpaired, Mann-Whitney-unpaired-Wilcoxon, ANOVA-one-way, default is Kruskal-Wallis")
    parser.add_option("", "--order", dest="order", default=None, help="column number to order output by, default is last column")
    parser.add_option("", "--direction", dest="direction", default="asc", help="direction of order. 'asc' for ascending order, 'desc' for descending order, default is asc")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if (opts.input != '-') and (not os.path.isfile(opts.input)):
        sys.stderr.write("ERROR: input data missing\n")
        return 1
    if opts.format not in ['text', 'biom']:
        sys.stderr.write("ERROR: invalid input format\n")
        return 1
    if (not opts.rlib) and ('KB_PERL_PATH' in os.environ):
        opts.rlib = os.environ['KB_PERL_PATH']
    if not opts.rlib:
        sys.stderr.write("ERROR: missing path to R libs\n")
        return 1
    if opts.direction not in ['asc', 'desc']:
        sys.stderr.write("ERROR: invalid sort direction\n")
        return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # get inputs
    tmp_in  = 'tmp_'+random_str()+'.txt'
    tmp_out = 'tmp_'+random_str()+'.txt'
    tmp_hdl = open(tmp_in, 'w')
    mg_list = []
    groups  = []
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        if opts.format == 'biom':
            try:
                indata = json.loads(indata)
                biom_to_tab(indata, tmp_hdl)
                mg_list = map(lambda x: x['id'], indata['columns'])
                try:
                    groups = map(lambda x: x['group'], indata['columns'])
                except:
                    pass
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
    
    # get groups if not in BIOM
    if not groups:
        try:
            grdata = json.load(open(opts.groups, 'r')) if os.path.isfile(opts.groups) else json.loads(opts.groups)
        except:
            sys.stderr.write("ERROR: unable to parse groups JSON\n")
            return 1
        for mg in mg_list:
            found_gr = None
            for gr in grdata.iterkeys():
                if mg in grdata[gr]:
                    found_gr = gr
                    break
            if found_gr:
                groups.append(found_gr)
            else:
                sys.stderr.write("ERROR: metagenome %s not in a group\n"%mg)
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
    stat_test="%s",
    order_by=%s,
    order_decreasing=%s,
    my_grouping=%s
))"""%(opts.rlib, tmp_in, tmp_out, fig_out, opts.stat_test, order_by, order_desc, group_str)
    execute_r(r_cmd)
    
    # output results
    results = open(tmp_out, 'r').read()
    os.remove(tmp_in)
    os.remove(tmp_out)
    safe_print(results)
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
