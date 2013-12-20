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
    mg-correlate-metadata [ --help, --input <input file or stdin>, --metadata <metadata field> ]

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
    parser.add_option("", "--metadata", dest="metadata", default=None, help="metadata field to correlate")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if (opts.input != '-') and (not os.path.isfile(opts.input)):
        sys.stderr.write("ERROR: input data missing\n")
        return 1
    if not opts.metadata:
        sys.stderr.write("ERROR: metadata field missing\n")
        return 1
    
    # load input
    try:
        data = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        biom = json.loads(data)
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1
            
    # get metadata
    meta = {}
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
    safe_print("# metagenomes used: %s"%",".join(meta.keys()))
    safe_print("# metadata field: %s"%opts.metadata)
    for a in annotation:
        l_meta = []
        l_anno = []
        for m in meta.iterkeys():
            l_meta.append(meta[m])
            l_anno.append(float(abund[m][a]))
        gradient, intercept, r_value, p_value, std_err = stats.linregress(l_meta, l_anno)
        if p_value < 0.05:
            safe_print("%s\t%.5f"%(a, p_value))
    
    return 0
    
if __name__ == "__main__":
    sys.exit( main(sys.argv) )
    