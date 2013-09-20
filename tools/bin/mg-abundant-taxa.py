#!/usr/bin/env python

import sys
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-abundant-taxa

VERSION
    %s

SYNOPSIS
    mg-abundant-taxa [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --id <metagenome id>, --level <taxon level>, --source <datasource>, --top <N lines to return>, --evalue <evalue negative exponent>, --identity <percent identity>, --length <alignment length> ]

DESCRIPTION
    Retrieve top abundant taxa for metagenome.
"""

posthelp = """
Output
    Tab-delimited list of taxon and abundance sorted by abundance (largest first). 'top' option controls number of rows returned.

EXAMPLES
    mg-abundant-taxa --id "kb|mg.287" --level genus --source RefSeq --top 20 --evalue 8

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--id", dest="id", default=None, help="KBase Metagenome ID")
    parser.add_option("", "--url", dest="url", default=API_URL, help="communities API url")
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")
    parser.add_option("", "--level", dest="level", default='species', help="taxon level to retrieve abundances for, default is species")
    parser.add_option("", "--source", dest="source", default='SEED', help="datasource to filter results by, default is SEED")
    parser.add_option("", "--top", dest="top", default=10, help="display only the top N taxa, default is 10")
    parser.add_option("", "--evalue", dest="evalue", default=5, help="negative exponent value for maximum e-value cutoff, default is 5")
    parser.add_option("", "--identity", dest="identity", default=60, help="percent value for minimum % identity cutoff, default is 60")
    parser.add_option("", "--length", dest="length", default=15, help="value for minimum alignment length cutoff, default is 15")
    
    # get inputs
    (opts, args) = parser.parse_args()
    opts.top = int(opts.top)
    if not opts.id:
        sys.stderr.write("ERROR: id required\n")
        return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # build url
    if opts.id.startswith('kb|'):
        opts.id = kbid_to_mgid(opts.id)
    params = [ ('id', opts.id),
               ('group_level', opts.level),
               ('source', opts.source),
               ('evalue', opts.evalue),
               ('identity', opts.identity),
               ('length', opts.length),
               ('result_type', 'abundance'),
               ('asynchronous', '1'),
               ('hide_metadata', '1') ]
    url = opts.url+'/matrix/organism?'+urllib.urlencode(params, True)

    # retrieve data
    top_ann = {}
    biom = async_rest_api(url, auth=token)
    for d in sorted(biom['data'], key=itemgetter(2), reverse=True):
        name = biom['rows'][d[0]]['id']
        if len(top_ann) >= opts.top:
            break
        top_ann[name] = d[2]
    
    # output data
    for k, v in sorted(top_ann.items(), key=itemgetter(1), reverse=True):
        sys.stdout.write("%s\t%d\n" %(k, v))
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
