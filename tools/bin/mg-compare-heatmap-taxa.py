#!/usr/bin/env python

import sys
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-compare-heatmap-taxa

VERSION
    %s

SYNOPSIS
    mg-compare-heatmap-taxa [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --ids <metagenome ids>, --level <taxon level>, --source <datasource>, --evalue <evalue negative exponent>, --identity <percent identity>, --length <alignment length>, --cluster <cv: ward, single, complete, mcquitty, median, centroid>, --distance <cv: bray-curtis, euclidean, maximum, manhattan, canberra, minkowski, difference> ]

DESCRIPTION
    Retrieve Dendogram Heatmap from taxanomic abundance profiles for multiple metagenomes.
"""

posthelp = """
Output
    Tab-delimited table of first 4 principal components for each metagenome.

EXAMPLES
    mg-compare-heatmap-taxa --ids "kb|mg.286,kb|mg.287,kb|mg.288,kb|mg.289" --level class --source RefSeq --cluster median --distance manhattan --evalue 8

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--ids", dest="ids", default=None, help="comma seperated list of KBase Metagenome IDs")
    parser.add_option("", "--url", dest="url", default=API_URL, help="communities API url")
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")
    parser.add_option("", "--level", dest="level", default='species', help="taxon level to retrieve abundances for, default is species")
    parser.add_option("", "--source", dest="source", default='SEED', help="datasource to filter results by, default is SEED")
    parser.add_option("", "--cluster", dest="cluster", default='ward', help="cluster function, one of: ward, single, complete, mcquitty, median, centroid, default is ward")
    parser.add_option("", "--distance", dest="distance", default='bray-curtis', help="distance function, one of: bray-curtis, euclidean, maximum, manhattan, canberra, minkowski, difference, default is bray-curtis")
    parser.add_option("", "--evalue", dest="evalue", default=5, help="negative exponent value for maximum e-value cutoff, default is 5")
    parser.add_option("", "--identity", dest="identity", default=60, help="percent value for minimum % identity cutoff, default is 60")
    parser.add_option("", "--length", dest="length", default=15, help="value for minimum alignment length cutoff, default is 15")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if not opts.ids:
        sys.stderr.write("ERROR: two or more ids required\n")
        return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # build url
    ids = opts.ids.split(',')
    if len(ids) < 2:
        sys.stderr.write("ERROR: two or more ids required\n")
        return 1
    id_list = kbids_to_mgids(ids)
    params = [ ('group_level', opts.level), 
               ('source', opts.source),
               ('evalue', opts.evalue),
               ('identity', opts.identity),
               ('length', opts.length),
               ('result_type', 'abundance'),
               ('asynchronous', '1'),
               ('hide_metadata', '1') ]
    for i in id_list:
        params.append(('id', i))
    burl = opts.url+'/matrix/organism?'+urllib.urlencode(params, True)
    hurl = opts.url+'/compute/heatmap'

    # retrieve data
    biom = async_rest_api(burl, auth=token)
    rows = [r['id'] for r in biom['rows']]
    cols = [c['id'] for c in biom['columns']]
    matrix = sparse_to_dense(biom['data'], len(rows), len(cols))
    hdata = {"cluster": opts.cluster, "distance": opts.distance, "columns": cols, "rows": rows, "data": matrix}
    hmap = obj_from_url(hurl, data=json.dumps(hdata, separators=(',',':')))
    
    # output data
    safe_print(json.dumps(hmap, separators=(', ',': '), indent=4)+'\n')
    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
