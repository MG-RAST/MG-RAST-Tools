#!/usr/bin/env python

import os
import sys
import json
from collections import defaultdict
from optparse import OptionParser
from scipy import stats
from mglib import *

prehelp = """
NAME
    mg-correlate-metadata

VERSION
    %s

SYNOPSIS
    mg-correlate-metadata [ --help, --input <input file or stdin>, --format <cv: 'text' or 'biom'>, --metadata <metadata field>, --groups <json string or filepath>, --group_pos <integer>, --cutoff <float> ]

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

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--input", dest="input", default='-', help="input: filename or stdin (-), default is stdin")
    parser.add_option("", "--format", dest="format", default='text', help="input format: 'text' for tabbed table, 'biom' for BIOM format, default is text")
    parser.add_option("", "--metadata", dest="metadata", default=None, help="metadata field to correlate")
    parser.add_option("", "--groups", dest="groups", default=None, help="list of metadata groups in JSON or tabbed format - either as input string or filename")
    parser.add_option("", "--group_pos", dest="group_pos", type="int", default=1, help="position of metadata group to use, default is 1 (first)")
    parser.add_option("", "--cutoff", dest="cutoff", default=None, help="only show p-value less than this, default show all")
    
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
    
    # load input
    try:
        data = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        biom = json.loads(data)
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1
            
    # get metadata
    meta = {}
    keep = []
    skip = []
    try:
        for col in biom['columns']:
            value = None
            # find metadata value
            for v in col['metadata'].itervalues():
                if ('data' in v) and (opts.metadata in v['data']):
                    value = v['data'][opts.metadata]
            # only accept numeric
            try:
                meta[col['id']] = float(value)
                keep.append(col['id'])
            except:
                skip.append(col['id'])
    except:
        sys.stderr.write("ERROR: input BIOM data missing metadata\n")
        return 1
        
    # get annotations
    abund = defaultdict(dict)
    if biom['matrix_type'] == 'sparse':
        matrix = sparse_to_dense(biom['data'], biom['shape'][0], biom['shape'][1])
    else:
        matrix = biom['data']
    for c, col in enumerate(biom['columns']):
        # only use valid metagenomes
        if col['id'] in meta:
            for r, row in enumerate(biom['rows']):
                abund[col['id']][row['id']] = matrix[r][c]
    
    # check correlation
    annotation = [r['id'] for r in biom['rows']]
    annotation.sort()
    if len(skip) > 0:
        safe_print("# metagenomes skipped: %s\n"%",".join(skip))
    safe_print("\t%s\tr-value\tp-value\n"%"\t".join(keep))
    for a in annotation:
        l_meta = []
        l_anno = []
        for m in keep:
            l_meta.append(meta[m])
            l_anno.append(float(abund[m][a]))
        gradient, intercept, r_value, p_value, std_err = stats.linregress(l_meta, l_anno)
        oline = "%s\t%s\t%.5f\t%.5f\n"%(a, "\t".join([str(abund[m][a]) for m in keep]), r_value, p_value)
        if opts.cutoff:
            if p_value < opts.cutoff:
                safe_print(oline)
        else:
            safe_print(oline)
    
    return 0
    
if __name__ == "__main__":
    sys.exit( main(sys.argv) )
    