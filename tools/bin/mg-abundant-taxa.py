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
    mg-abundant-taxa [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --id <metagenome id>, --level <taxon level>, --source <datasource>, --filter_name <taxon name>, --filter_level <taxon level>, --top <N lines to return>, --evalue <evalue negative exponent>, --identity <percent identity>, --length <alignment length> ]

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
    parser.add_option("", "--filter_name", dest="filter_name", default=None, help="taxon name to filter by")
    parser.add_option("", "--filter_level", dest="filter_level", default=None, help="taxon level to filter by")
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
    if (opts.filter_name and (not opts.filter_level)) or ((not opts.filter_name) and opts.filter_level):
        sys.stderr.write("ERROR: both --filter_level and --filter_name need to be used together\n")
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
    
    # get sub annotations
    sub_ann = set()
    if opts.filter_name and opts.filter_level:
        params = [ ('filter', opts.filter_name),
                   ('filter_level', opts.filter_level),
                   ('min_level', opts.level),
                   ('version', '1') ]
        url = opts.url+'/m5nr/taxonomy?'+urllib.urlencode(params, True)
        data = obj_from_url(url)
        sub_ann = set( map(lambda x: x[opts.level], data['data']) )
    
    # sort data
    for d in sorted(biom['data'], key=itemgetter(2), reverse=True):
        name = biom['rows'][d[0]]['id']
        if len(top_ann) >= opts.top:
            break
        if sub_ann and (name not in sub_ann):
            continue
        top_ann[name] = d[2]
    
    # output data
    for k, v in sorted(top_ann.items(), key=itemgetter(1), reverse=True):
        safe_print("%s\t%d\n" %(k, v))
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
