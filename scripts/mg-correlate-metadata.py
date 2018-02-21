#!/usr/bin/env python

import os
import sys
import json
from collections import defaultdict
from optparse import OptionParser
import numpy as np
from scipy import stats
from mglib import *

prehelp = """
NAME
    mg-correlate-metadata

VERSION
    %s

SYNOPSIS
    mg-correlate-metadata [ --help, --input <input file or stdin>, --format <cv: 'text' or 'biom'>, --output <cv: 'full', 'minimum', 'biom'>, --metadata <metadata field>, --groups <json string or filepath>, --group_pos <integer>, --cutoff <float>, --fdr <boolean> ]

DESCRIPTION
    Identify annotations with a significant correlation to a given metadata field using linear regression.
"""

posthelp = """
Input
    1. BIOM format of abundance profiles with metadata.
    2. Groups in JSON format - either as input string or filename

Output
    Tabbed table of annotation and correlation p-value.

EXAMPLES
    mg-compare-taxa --ids 'mgm4441619.3,mgm4441656.4,mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3' --level class --source RefSeq --format biom | mg-correlate-metadata --input - --metadata latitude --format biom

SEE ALSO
    -

AUTHORS
    %s
"""

def calculate_fdr(p_values):
    p_values = np.atleast_1d(p_values)
    n_samples = p_values.size
    order = p_values.argsort()
    sp_values = p_values[order]
    # compute q while in ascending order
    q = np.minimum(1, n_samples * sp_values / np.arange(1, n_samples + 1))
    for i in range(n_samples - 1, 0, - 1):
        q[i - 1] = min(q[i], q[i - 1])
    # reorder the results
    inverse_order = np.arange(n_samples)
    inverse_order[order] = np.arange(n_samples)
    return q[inverse_order]

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--input", dest="input", default='-', help="input: filename or stdin (-), default is stdin")
    parser.add_option("", "--format", dest="format", default='biom', help="input format: 'text' for tabbed table, 'biom' for BIOM format, default is biom")
    parser.add_option("", "--output", dest="output", default='biom', help="output format: 'full' for tabbed abundances and stats, 'minimum' for tabbed stats only, 'biom' for BIOM format, default is biom")
    parser.add_option("", "--metadata", dest="metadata", default=None, help="metadata field to correlate, only for 'biom' input")
    parser.add_option("", "--groups", dest="groups", default=None, help="list of groups in JSON or tabbed format - either as input string or filename")
    parser.add_option("", "--group_pos", dest="group_pos", type="int", default=1, help="position of group to use, default is 1 (first)")
    parser.add_option("", "--cutoff", dest="cutoff", default=None, help="only show p-value less than this, default show all")
    parser.add_option("", "--fdr", dest="fdr", action="store_true", default=False, help="output FDR for computed p-values, default is off")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if (opts.input != '-') and (not os.path.isfile(opts.input)):
        sys.stderr.write("ERROR: input data missing\n")
        return 1
    if opts.format not in ['text', 'biom']:
        sys.stderr.write("ERROR: invalid input format\n")
        return 1
    if opts.output not in ['full', 'minimum', 'biom']:
        sys.stderr.write("ERROR: invalid output format\n")
        return 1
    
    # parse inputs
    biom = None
    rows = []
    cols = []
    data = []    
    groups = []
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        if opts.format == 'biom':
            try:
                biom = json.loads(indata)
                rows, cols, data = biom_to_matrix(biom)
                if opts.metadata:
                    groups = metadata_from_biom(biom, opts.metadata)
            except:
                sys.stderr.write("ERROR: input BIOM data not correct format\n")
                return 1
        else:
            rows, cols, data = tab_to_matrix(indata)
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1
    
    # get groups if not in BIOM metadata and option used
    if (len(groups) == 0) and opts.groups:
        # is it json ?
        ## example of 2 group sets in json format
        ## [ {"group1": ["mg_id_1", "mg_id_2"], "group2": ["mg_id_3", "mg_id_4", "mg_id_5"]},
        ##   {"group1": ["mg_id_1", "mg_id_2", "mg_id_3"], "group2": ["mg_id_4", "mg_id_5"]} ]
        try:
            gdata = json.load(open(opts.groups, 'r')) if os.path.isfile(opts.groups) else json.loads(opts.groups)
            if opts.group_pos > len(gdata):
                sys.stderr.write("ERROR: position (%d) of metadata is out of bounds\n"%opts.group_pos)
                return 1
            for m in cols:
                found_g = None
                for g, mgs in gdata[opts.group_pos-1].items():
                    if m in mgs:
                        found_g = g
                        break
                if found_g:
                    groups.append(found_g)
                else:
                    sys.stderr.write("ERROR: metagenome %s missing metadata\n"%m)
                    return 1                  
        # no - its tabbed
        except:
            gtext = open(opts.groups, 'r').read() if os.path.isfile(opts.groups) else opts.groups
            grows, gcols, gdata = tab_to_matrix(gtext)
            if opts.group_pos > len(gdata[0]):
                sys.stderr.write("ERROR: position (%d) of metadata is out of bounds\n"%opts.group_pos)
            for m in cols:
                try:
                    midx = gcols.index(m)
                    groups.append(gdata[midx][opts.group_pos-1])
                except:
                    sys.stderr.write("ERROR: metagenome %s missing metadata\n"%m)
                    return 1
    
    # validate metadata
    if len(groups) != len(cols):
        sys.stderr.write("ERROR: Not all metagenomes have metadata\n")
        return 1
    try:
        groups = map(lambda x: float(x), groups)
    except:
        sys.stderr.write("ERROR: Metadata is not numeric\n")
        return 1
    
    # check correlation
    results = []
    pvalues = []
    for i, a in enumerate(rows): # annotations
        l_meta = []
        l_anno = []
        for j, m in enumerate(cols): # metagenomes
            l_meta.append(groups[j])
            l_anno.append(float(data[i][j]))
        gradient, intercept, r_value, p_value, std_err = stats.linregress(l_meta, l_anno)
        if biom and (opts.output == 'biom'):
            results.append([('r-value', r_value), ('p-value', p_value)])
            pvalues.append(p_value)
        else:
            if opts.output == 'full':
                l_result = [a]+[float(x) for x in data[i]]+[r_value, p_value]
            elif opts.output == 'minimum':
                l_result = [a, r_value, p_value]
            if (not opts.cutoff) or (opts.cutoff and (p_value < opts.cutoff)):
                results.append(l_result)
                pvalues.append(p_value)
    
    # calculate fdr
    if opts.fdr and pvalues:
        fdr_values = calculate_fdr(pvalues)
        for i, x in enumerate(fdr_values):
            results[i].append(('fdr', x) if biom and (opts.output == 'biom') else x)
    
    # output
    if biom and (opts.output == 'biom'):
        # add stats to row data, same order
        new_rows = []
        for i, robj in enumerate(biom['rows']):
            if not robj['metadata']:
                robj['metadata'] = {'correlate': results[i]}
            else:
                robj['metadata']['correlate'] = results[i]
            new_rows.append(robj)
        # update biom
        biom['id'] = biom['id']+'_corr'
        biom['rows'] = new_rows
        safe_print(json.dumps(biom)+'\n')
    else:
        header = ['r-value', 'p-value']
        if opts.output == 'full':
            header = header
        if opts.fdr:
            header.append('fdr')
        safe_print("\t%s\n"%"\t".join(header))
        for r in results:
            safe_print(r[0])
            for x in r[1:]:
                if int(x) == float(x):
                    safe_print("\t%d"%int(x))
                else:
                    safe_print("\t%.5f"%float(x))
            safe_print("\n")
    
    return 0
    
if __name__ == "__main__":
    sys.exit( main(sys.argv) )
    
