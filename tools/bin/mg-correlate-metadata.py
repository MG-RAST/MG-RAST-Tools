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
    mg-correlate-metadata [ --help, --input <input file or stdin>, --format <cv: 'text' or 'biom'>, --metadata <metadata field>, --groups <json string or filepath>, --group_pos <integer>, --output <cv: 'full' or 'minimum'>, --cutoff <float>, --fdr <boolean> ]

DESCRIPTION
    Identify annotations with a significant correlation to a given metadata field using linear regression.
"""

posthelp = """
Input
    BIOM format of abundance profiles with metadata.

Output
    Tabbed table of annotation and correlation p-value.

EXAMPLES
    mg-compare-taxa --ids 'mgm4441619.3,mgm4441656.4,mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3' --level class --source RefSeq --format biom | mg-correlate-metadata --input - --metadata latitude

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
    parser.add_option("", "--format", dest="format", default='text', help="input format: 'text' for tabbed table, 'biom' for BIOM format, default is text")
    parser.add_option("", "--metadata", dest="metadata", default=None, help="metadata field to correlate")
    parser.add_option("", "--groups", dest="groups", default=None, help="list of metadata groups in JSON or tabbed format - either as input string or filename")
    parser.add_option("", "--group_pos", dest="group_pos", type="int", default=1, help="position of metadata group to use, default is 1 (first)")
    parser.add_option("", "--output", dest="output", default='full', help="output format: 'full' for abundances and significance, 'minimum' for significance only, default is full")
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
    if opts.metadata:
        opts.group_pos = 1
    
    # load input / get metadata
    meta = {}
    keep = []
    rows = []
    cols = []
    data = []
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        if opts.format == 'biom':
            try:
                biom = json.loads(indata)
                rows, cols, data = biom_to_matrix(biom)
                if opts.metadata:
                    for c in biom['columns']:
                        value = None
                        for v in c['metadata'].itervalues():
                            if ('data' in v) and (opts.metadata in v['data']):
                                value = v['data'][opts.metadata]
                        try:
                            meta[c['id']] = float(value)
                            keep.append(c['id'])
                        except:
                            pass
            except:
                sys.stderr.write("ERROR: input BIOM data not correct format\n")
                return 1
        else:
            rows, cols, data = tab_to_matrix(indata)
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1
    
    # get groups if not in BIOM metadata and option used
    if (not meta) and opts.groups:
        gindx = opts.group_pos - 1
        # is it json ?
        try:
            gdata = json.load(open(opts.groups, 'r')) if os.path.isfile(opts.groups) else json.loads(opts.groups)
            if opts.group_pos > len(gdata):
                sys.stderr.write("ERROR: group pos (%d) is greater than group size (%d)\n"%(opts.group_pos, len(gdata)))
                return 1
            for mg in cols:
                for g in gdata[gindx].iterkeys():
                    if mg in gdata[gindx][g]:
                        meta[mg] = g
        # no - its tabbed
        except:
            gtext = open(opts.groups, 'r').read() if os.path.isfile(opts.groups) else opts.groups
            for line in gtext.strip().split("\n")[1:]:
                parts = line.strip().split("\t")
                mgid  = parts.pop(0)
                try:
                    meta[mgid] = float(parts[gindx])
                    keep.append(mgid)
                except:
                    pass
    
    # get annotations
    abund = defaultdict(dict)
    for i, c in enumerate(cols):
        # only use valid metagenomes
        if c in meta:
            for j, r in enumerate(rows):
                abund[c][r] = data[j][i]
    
    # check correlation
    annotation = sorted(rows)
    results = []
    pvalues = []
    for a in annotation:
        l_meta = []
        l_anno = []
        for m in keep:
            l_meta.append(meta[m])
            l_anno.append(float(abund[m][a]))
        gradient, intercept, r_value, p_value, std_err = stats.linregress(l_meta, l_anno)
        if opts.output == 'full':
            l_result = [a]+[float(abund[m][a]) for m in keep]+[r_value, p_value]
        else:
            l_result = [a, r_value, p_value]
        if (not opts.cutoff) or (opts.cutoff and (p_value < opts.cutoff)):
            results.append(l_result)
            pvalues.append(p_value)
    
    # calculate fdr
    if opts.fdr and pvalues:
        fdr_values = calculate_fdr(pvalues)
        for i, x in enumerate(fdr_values):
            results[i].append(x)
    
    # output
    header = ['r-value', 'p-value']
    if opts.output == 'full':
        header = keep+header
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
    