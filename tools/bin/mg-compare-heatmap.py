#!/usr/bin/env python

import sys
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-compare-heatmap

VERSION
    %s

SYNOPSIS
    mg-compare-heatmap [ --help, --input <input file or stdin>, --format <cv: 'text' or 'biom'>, --cluster <cv: ward, single, complete, mcquitty, median, centroid>, --distance <cv: bray-curtis, euclidean, maximum, manhattan, canberra, minkowski, difference> ]

DESCRIPTION
    Retrieve Dendogram Heatmap from taxanomic abundance profiles for multiple metagenomes.
"""

posthelp = """
Input
    Tab-delimited table of abundance profiles, metagenomes in columns and annotation in rows.
    OR
    BIOM format of abundance profiles.

Output
    JSON struct containing ordered distances for metagenomes and annotations, along with dendogram data

EXAMPLES
    mg-compare-taxa --ids "kb|mg.286,kb|mg.287,kb|mg.288,kb|mg.289" --level class --source RefSeq --format text | mg-compare-heatmap --input - --format text --cluster median --distance manhattan

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--url", dest="url", default=API_URL, help="communities API url")
    parser.add_option("", "--input", dest="input", default='-', help="input: filename or stdin (-), default is stdin")
    parser.add_option("", "--format", dest="format", default='text', help="input format: 'text' for tabbed table, 'biom' for BIOM format, default is text")
    parser.add_option("", "--cluster", dest="cluster", default='ward', help="cluster function, one of: ward, single, complete, mcquitty, median, centroid, default is ward")
    parser.add_option("", "--distance", dest="distance", default='bray-curtis', help="distance function, one of: bray-curtis, euclidean, maximum, manhattan, canberra, minkowski, difference, default is bray-curtis")

    # get inputs
    (opts, args) = parser.parse_args()
    if (opts.input != '-') and (not os.path.isfile(opts.input)):
        sys.stderr.write("ERROR: input data missing\n")
        return 1
    if opts.format not in ['text', 'biom']:
        sys.stderr.write("ERROR: invalid input format\n")
        return 1
    
    # parse inputs
    rows = []
    cols = []
    data = []
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        if opts.format == 'biom':
            try:
                biom = json.loads(indata)
                rows = [r['id'] for r in biom['rows']]
                cols = [c['id'] for c in biom['columns']]
                data = sparse_to_dense(biom['data'], len(rows), len(cols))
            except:
                sys.stderr.write("ERROR: input BIOM data not correct format\n")
                return 1
        else:
            lines = indata.split('\n')
            cols = lines[0].strip().split('\t')
            for line in lines[1:]:
                parts = line.strip().split('\t')
                first = parts.pop(0)
                if len(cols) == len(parts):
                    rows.append(first)
                    data.append(parts)
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1

    # retrieve data
    post = {"cluster": opts.cluster, "distance": opts.distance, "columns": cols, "rows": rows, "data": data}
    hmap = obj_from_url(opts.url+'/compute/heatmap', data=json.dumps(post, separators=(',',':')))
    
    # output data
    safe_print(json.dumps(hmap, separators=(', ',': '), indent=4)+'\n')
    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
