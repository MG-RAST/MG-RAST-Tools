#!/usr/bin/env python

import os
import sys
import json
from argparse import ArgumentParser
from mglib import biom_to_matrix, metadata_from_biom, tab_to_matrix, obj_from_url, AUTH_LIST, VERSION, API_URL

prehelp = """
NAME
    mg-compare-pcoa

VERSION
    %s

SYNOPSIS
    mg-compare-pcoa [ --help, --input <input file or stdin>, --output <output file or stdout>, --format <cv: 'text' or 'biom'>, --distance <cv: bray-curtis, euclidean, maximum, manhattan, canberra, minkowski, difference>, --metadata <metadata field>, --name <boolean>, --normalize <boolean> ]

DESCRIPTION
    Retrieve PCoA (Principal Coordinate Analysis) from abundance profiles for multiple metagenomes.
"""

posthelp = """
Input
    Tab-delimited table of abundance profiles, metagenomes in columns and annotation in rows.
    OR
    BIOM format of abundance profiles.

Output
    Tab-delimited table of first 4 principal components for each metagenome.

EXAMPLES
    mg-compare-taxa --ids "mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3" --level class --source RefSeq --format text | mg-compare-pcoa --input - --format text --distance manhattan

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_argument("--url", dest="url", default=API_URL, help="communities API url")
    parser.add_argument("--input", dest="input", default='-', help="input: filename or stdin (-), default is stdin")
    parser.add_argument("--output", dest="output", default='-', help="output: filename or stdout (-), default is stdout")
    parser.add_argument("--format", dest="format", default='biom', help="input / output format: 'text' for tabbed table, 'biom' for BIOM / json format, default is biom")
    parser.add_argument("--metadata", dest="metadata", default=None, help="metadata field to group by, only for 'biom' input")
    parser.add_argument("--distance", dest="distance", default='bray-curtis', help="distance metric, one of: bray-curtis, euclidean, maximum, manhattan, canberra, minkowski, difference, default is bray-curtis")
    parser.add_argument("--name", dest="name", type=int, default=0, help="label columns by name, default is by id: 1=true, 0=false")
    parser.add_argument("--normalize", dest="normalize", type=int, default=0, help="normalize the input data, default is off: 1=true, 0=false")
    
    # get inputs
    opts = parser.parse_args()
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
    groups = []
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        if opts.format == 'biom':
            try:
                biom = json.loads(indata)
                col_name = True if opts.name == 1 else False
                rows, cols, data = biom_to_matrix(biom, col_name=col_name)
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
    
    # get group map
    gmap = {}
    for i, g in enumerate(groups):
        if g != 'null':
            gmap[cols[i]] = g
    
    # retrieve data
    raw  = '0' if opts.normalize == 1 else '1'
    post = {"raw": raw, "distance": opts.distance, "columns": cols, "rows": rows, "data": data}
    pcoa = obj_from_url(opts.url+'/compute/pcoa', data=json.dumps(post, separators=(',',':')))
    
    # output data
    if (not opts.output) or (opts.output == '-'):
        out_hdl = sys.stdout
    else:
        out_hdl = open(opts.output, 'w')
    
    if opts.format == 'biom':
        for i in range(len(pcoa['data'])):
            pcoa['data'][i]['group'] = gmap[ pcoa['data'][i]['id'] ] if pcoa['data'][i]['id'] in gmap else ""
        out_hdl.write(json.dumps(pcoa)+"\n")
    else:
        out_hdl.write("ID\tGroup\tPC1\tPC2\tPC3\tPC4\n")
        for d in pcoa['data']:
            out_hdl.write("%s\t%s\t%s\n" %(d['id'], gmap[d['id']] if (d['id'] in gmap) else "", "\t".join(map(str, d['pco'][0:4]))))
    
    out_hdl.close()
    return 0
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))
