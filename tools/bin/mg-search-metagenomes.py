#!/usr/bin/env python

import sys
import time
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-search-metagenomes

VERSION
    %s

SYNOPSIS
    mg-search-metagenomes [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --order <field name> --direction <cv: 'asc', 'desc'> --match <cv: 'all, 'any'> --status <cv: 'both', 'public', 'private'> --verbosity <cv: 'minimal', 'full'> %s ]

DESCRIPTION
    Retrieve list of metagenomes based on search criteria.
"""

posthelp = """
Output
    List of metagenomes.

EXAMPLES
    mg-search-metagenomes --help

SEE ALSO
    -

AUTHORS
    %s
"""

search_opts = " ".join( map(lambda x: "--%s <query text>"%x, SEARCH_FIELDS) )

def display_search(data, fields):
    for d in data:
        row = [d[f] for f in fields]
        safe_print("\t".join([r if ord(r) < 128 else '?' for r in row])+"\n")

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%(VERSION, search_opts), epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--url", dest="url", default=API_URL, help="communities API url")
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")
    parser.add_option("", "--workspace", dest="workspace", default=None, help="Save results in a workspace with this name")
    parser.add_option("", "--save_name", dest="save_name", default=None, help="Name of object to create in workspace")
    parser.add_option("", "--order", dest="order", default=None, help="field metagenomes are ordered by, default is no ordering")
    parser.add_option("", "--direction", dest="direction", default="asc", help="direction of order. 'asc' for ascending order, 'desc' for descending order, default is asc")
    parser.add_option("", "--match", dest="match", default="all", help="search logic. 'all' for metagenomes that match all search parameters, 'any' for metagenomes that match any search parameters, default is all")
    parser.add_option("", "--status", dest="status", default="public", help="types of metagenomes to return. 'both' for all data (public and private), 'public' for public data, 'private' for users private data, default is public")
    parser.add_option("", "--verbosity", dest="verbosity", default='minimal', help="amount of information to display. use keyword 'minimal' for id and name, use keyword 'full' for MIxS GSC metadata, default is minimal")
    for sfield in SEARCH_FIELDS:
        parser.add_option("", "--"+sfield, dest=sfield, default=None, help="search parameter: query string for "+sfield)
    
    # get inputs
    (opts, args) = parser.parse_args()
    
    # get auth
    token = get_auth_token(opts)
    
    # build call url
    params = [ ('limit', '100'),
               ('match', opts.match),
               ('status', opts.status),
               ('verbosity', opts.verbosity if opts.verbosity == 'minimal' else 'mixs') ]
    for sfield in SEARCH_FIELDS:
        if hasattr(opts, sfield) and getattr(opts, sfield):
            params.append( (sfield, getattr(opts, sfield)) )
    if opts.order:
        params.append( ('order', opts.order) )
        params.append( ('direction', opts.direction) )
    url = opts.url+'/metagenome?'+urllib.urlencode(params, True)
    
    # retrieve data
    fields = ['id']
    result = obj_from_url(url, auth=token)
    if len(result['data']) == 0:
        sys.stdout.write("No results found for the given search parameters\n")
        return 0
    for sfield in SEARCH_FIELDS:
        if sfield in result['data'][0]:
            fields.append(sfield)
    fields.append('status')
    ids = [d['id'] for d in result['data']]
    
    # output header
    safe_print("\t".join(fields)+"\n")
    # output rows
    display_search(result['data'], fields)
    while result['next']:
        url = result['next']
        result = obj_from_url(url, auth=token)
        ids.extend([d['id'] for d in result['data']])
        display_search(result['data'], fields)
    
    # output workspace
    if opts.workspace and opts.save_name:
        sys.stdout.write('\n')
        ws_type = 'Communities.Collection-1.0'
        ws_obj = {'name': opts.save_name, 'type': 'metagenomes', 'created': time.strftime("%Y-%m-%d %H:%M:%S"), 'members': []}
        for i in ids:
            ws_obj['members'].append({'ID': i, 'URL': opts.url+'/metagenome/'+i})
        load_to_ws(opts.workspace, ws_type, opts.save_name, json.dumps(ws_obj))
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
