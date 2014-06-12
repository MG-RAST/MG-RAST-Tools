#!/usr/bin/env python

import sys
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-extract-sequences

VERSION
    %s

SYNOPSIS
    mg-extract-sequences [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --level <function level>, --source <datasource>, --evalue <evalue negative exponent>, --identity <percent identity>, --length <alignment length>, --status <cv: 'both', 'public', 'private'> --verbosity <cv: 'minimal', 'full'> %s ]

DESCRIPTION
    Retrieve annotated sequences from metagenomes filtered by function name and metadata.
"""

posthelp = """
Output
    Tab-delimited list of: m5nr id, dna sequence, semicolon seperated list of annotations, sequence id

EXAMPLES
    mg-extract-sequences --function "protease" --biome "marine"

SEE ALSO
    -

AUTHORS
    %s
"""

search_opts = " ".join( map(lambda x: "--%s <query text>"%x, SEARCH_FIELDS) )

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%(VERSION, search_opts), epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--url", dest="url", default=API_URL, help="API url")
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")
    parser.add_option("", "--level", dest="level", default='function', help="function level to filter by")
    parser.add_option("", "--source", dest="source", default='Subsystems', help="datasource to filter results by, default is Subsystems")
    parser.add_option("", "--evalue", dest="evalue", default=5, help="negative exponent value for maximum e-value cutoff, default is 5")
    parser.add_option("", "--identity", dest="identity", default=60, help="percent value for minimum % identity cutoff, default is 60")
    parser.add_option("", "--length", dest="length", default=15, help="value for minimum alignment length cutoff, default is 15")
    parser.add_option("", "--status", dest="status", default="public", help="types of metagenomes to return. 'both' for all data (public and private), 'public' for public data, 'private' for users private data, default is public")
    for sfield in SEARCH_FIELDS:
        parser.add_option("", "--"+sfield, dest=sfield, default=None, help="search parameter: query string for "+sfield)
    
    # get inputs
    (opts, args) = parser.parse_args()
    
    # get auth
    token = get_auth_token(opts)

    # build url for metagenome query
    params = [ ('limit', '100'),
               ('verbosity', 'minimal'),
               ('match', 'all'),
               ('status', opts.status) ]
    for sfield in SEARCH_FIELDS:
        if hasattr(opts, sfield) and getattr(opts, sfield):
            params.append( (sfield, getattr(opts, sfield)) )
    url = opts.url+'/metagenome?'+urllib.urlencode(params, True)

    # retrieve query results
    result = obj_from_url(url, auth=token)
    if len(result['data']) == 0:
        sys.stdout.write("No results found for the given search parameters\n")
        return 0
    mgids = set( map(lambda x: x['id'], result['data']) )
    while result['next']:
        url = result['next']
        result = obj_from_url(url, auth=token)
        if len(result['data']) == 0:
            break
        for d in result['data']:
            mgids.add(d['id'])

    # get sequences for mgids
    for mg in mgids:
        params = [ ('source', opts.source),
                   ('evalue', opts.evalue),
                   ('identity', opts.identity),
                   ('length', opts.length) ]
        if (opts.source in ['Subsystems', 'KO', 'NOG', 'COG']) and (opts.level != 'function'):
            params.append(('type', 'ontology'))
        else:
            params.append(('type', 'function'))
        if opts.function:
            params.append(('filter', opts.function))
            if opts.level:
                params.append(('filter_level', opts.level))
        url = opts.url+'/annotation/sequence/'+mg+'?'+urllib.urlencode(params, True)
        # output data
        safe_print('Results from '+mg+":\n")
        stdout_from_url(url, auth=token)
    
    return 0
    
if __name__ == "__main__":
    sys.exit( main(sys.argv) )
