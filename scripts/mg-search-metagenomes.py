#!/usr/bin/env python

import sys
from argparse import ArgumentParser
from mglib import get_auth_token, SEARCH_FIELDS, urlencode, VERSION, AUTH_LIST, API_URL, obj_from_url, safe_print

prehelp = """
NAME
    mg-search-metagenomes

VERSION
    %s

SYNOPSIS
    mg-search-metagenomes [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --order <field name> --direction <cv: 'asc', 'desc'> --match <cv: 'all, 'any'> --public ]

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

search_opts = " ".join(map(lambda x: "--%s <query text>"%x, SEARCH_FIELDS))

def display_search(data, fields):
    for d in data:
        row = []
        for f in fields:
            if f not in d:
                row.append("-")
                continue
            try:
                row.append(str(d[f]))
            except:
                row.append("".join([x if ord(x) < 128 else '?' for x in d[f]]))
        safe_print("\t".join(row)+"\n")

def main(args):
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%(VERSION, search_opts), epilog=posthelp%AUTH_LIST)
    parser.add_argument("--url", dest="url", default=API_URL, help="communities API url")
    parser.add_argument("--user", dest="user", default=None, help="OAuth username")
    parser.add_argument("--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_argument("--token", dest="token", default=None, help="OAuth token")
    parser.add_argument("--limit", dest="limit", type=int, default=15, help="Number of results to show, if > 50 will use paginated queries to get all, default 15")
    parser.add_argument("--order", dest="order", default=None, help="field metagenomes are ordered by, default is no ordering")
    parser.add_argument("--direction", dest="direction", default="asc", help="direction of order. 'asc' for ascending order, 'desc' for descending order, default is asc")
    parser.add_argument("--public", dest="public", action="store_true", default=False, help="return both private and pubulic data if using authenticated search, default is private only.  Non-authenticated search only returns public.")
    parser.add_argument("--match", dest="match", default="all", help="search logic. 'all' for metagenomes that match all search parameters, 'any' for metagenomes that match any search parameters, default is all")
    parser.add_argument("--status", dest="status", default="public", help="types of metagenomes to return. 'both' for all data (public and private), 'public' for public data, 'private' for users private data, default is public")
    parser.add_argument("--verbosity", dest="verbosity", default='minimal', help="amount of information to display. use keyword 'minimal' for id and name, use keyword 'full' for MIxS GSC metadata, default is minimal")
    for sfield in SEARCH_FIELDS:
        parser.add_argument("--"+sfield, dest=sfield, default=None, help="search parameter: query string for "+sfield)
    
    # get inputs
    opts = parser.parse_args()
    
    # get auth
    token = get_auth_token(opts)
    
    # build call url
    total = 0
    maxLimit = 50
    params = [ ('limit', opts.limit if opts.limit < maxLimit else maxLimit),
               ('public', 'yes' if opts.public or (not token) else 'no') ]
    for sfield in SEARCH_FIELDS:
        if hasattr(opts, sfield) and getattr(opts, sfield):
            params.append((sfield, getattr(opts, sfield)))
    if opts.order:
        params.append(('order', opts.order))
        params.append(('direction', opts.direction))
    url = opts.url+'/search?'+urlencode(params, True)
    
    # retrieve data
    fields = ['metagenome_id', 'public'] + SEARCH_FIELDS
    result = obj_from_url(url, auth=token)
    found = len(result['data'])
    if found == 0:
        sys.stdout.write("No results found for the given search parameters\n")
        return 0
    total += found
    
    # output header
    safe_print("\t".join(fields)+"\n")
    # output rows
    display_search(result['data'], fields)
    
    while ('next' in result) and result['next'] and (total < opts.limit):
        url = result['next']
        result = obj_from_url(url, auth=token)
        total += len(result['data'])
        display_search(result['data'], fields)
    
    return 0
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))
