#!/usr/bin/env python

import os
import sys
import json
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-compare-heatmap

VERSION
    %s

SYNOPSIS
    mg-compare-heatmap [ --help, --input <input file or stdin>, --output <output file or stdout>, --format <cv: 'text' or 'biom'>, --cluster <cv: ward, single, complete, mcquitty, median, centroid>, --distance <cv: bray-curtis, euclidean, maximum, manhattan, canberra, minkowski, difference>, --name <boolean>, --normalize <boolean> ]

DESCRIPTION
    Retrieve Dendogram Heatmap from abundance profiles for multiple metagenomes.
"""

posthelp = """
Input
    Tab-delimited table of abundance profiles, metagenomes in columns and annotation in rows.
    OR
    BIOM format of abundance profiles.

Output
    JSON struct containing ordered distances for metagenomes and annotations, along with dendogram data.

EXAMPLES
    mg-compare-taxa --ids "mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3" --level class --source RefSeq --format text | mg-compare-heatmap --input - --format text --cluster median --distance manhattan

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
    parser.add_option("", "--output", dest="output", default='-', help="output: filename or stdout (-), default is stdout")
    parser.add_option("", "--format", dest="format", default='biom', help="input format: 'text' for tabbed table, 'biom' for BIOM format, default is biom")
    parser.add_option("", "--cluster", dest="cluster", default='ward', help="cluster function, one of: ward, single, complete, mcquitty, median, centroid, default is ward")
    parser.add_option("", "--distance", dest="distance", default='bray-curtis', help="distance function, one of: bray-curtis, euclidean, maximum, manhattan, canberra, minkowski, difference, default is bray-curtis")
    parser.add_option("", "--name", dest="name", type="int", default=0, help="label columns by name, default is by id: 1=true, 0=false")
    parser.add_option("", "--normalize", dest="normalize", type="int", default=0, help="normalize the input data, default is off: 1=true, 0=false")

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
                rows, cols, data = biom_to_matrix(biom, col_name=opts.name)
            except:
                sys.stderr.write("ERROR: input BIOM data not correct format\n")
                return 1
        else:
            rows, cols, data = tab_to_matrix(indata)
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1

    # retrieve data
    raw  = '0' if opts.normalize else '1'
    post = {"raw": raw, "cluster": opts.cluster, "distance": opts.distance, "columns": cols, "rows": rows, "data": data}
    hmap = obj_from_url(opts.url+'/compute/heatmap', data=json.dumps(post, separators=(',',':')))
    
    # output data
    if (not opts.output) or (opts.output == '-'):
        out_hdl = sys.stdout
    else:
        out_hdl = open(opts.output, 'w')
    
    out_hdl.write(json.dumps(hmap, separators=(', ',': '), indent=4)+"\n")
    out_hdl.close()
    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
