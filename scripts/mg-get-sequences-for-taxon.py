#!/usr/bin/env python

import sys
from argparse import ArgumentParser
from mglib import VERSION, AUTH_LIST, API_URL, urlencode, stdout_from_url, get_auth_token

prehelp = """
NAME
    mg-get-sequences-for-taxon

VERSION
    %s

SYNOPSIS
    mg-get-sequences-for-taxon [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --id <metagenome id>, --name <taxon name>, --level <taxon level>, --source <datasource>, --evalue <evalue negative exponent>, --identity <percent identity>, --length <alignment length> ]

DESCRIPTION
    Retrieve taxa annotated sequences for a metagenome filtered by taxon containing inputted name.
"""

posthelp = """
Output
    Tab-delimited list of: m5nr id, dna sequence, semicolon seperated list of annotations, sequence id

EXAMPLES
    mg-get-sequences-for-taxon --id "mgm4441680.3" --name Lachnospiraceae --level family --source RefSeq --evalue 8

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_argument("--id", dest="id", default=None, type=str, help="KBase Metagenome ID")
    parser.add_argument("--url", dest="url", default=API_URL, type=str, help="communities API url")
    parser.add_argument("--user", dest="user", default=None, type=str, help="OAuth username")
    parser.add_argument("--passwd", dest="passwd", default=None, type=str, help="OAuth password")
    parser.add_argument("--token", dest="token", default=None, type=str, help="OAuth token")
    parser.add_argument("--name", dest="name", default=None, type=str, help="taxon name to filter by")
    parser.add_argument("--level", dest="level", default=None, type=str, help="taxon level to filter by")
    parser.add_argument("--source", dest="source", default='SEED', type=str,  help="datasource to filter results by, default is SEED")
    parser.add_argument("--evalue", dest="evalue", default=5, type=float, help="negative exponent value for maximum e-value cutoff, default is 5")
    parser.add_argument("--identity", dest="identity", default=60, type=float, help="percent value for minimum %% identity cutoff, default is 60")
    parser.add_argument("--length", dest="length", default=15, type=float, help="value for minimum alignment length cutoff, default is 15")
    
    # get inputs
    opts = parser.parse_args()
    if not opts.id:
        sys.stderr.write("ERROR: id required\n")
        return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # build url
    params = [ ('source', opts.source),
               ('evalue', opts.evalue),
               ('identity', opts.identity),
               ('length', opts.length),
               ('type', 'organism') ]
    if opts.name:
        params.append(('filter', opts.name))
        if opts.level:
            params.append(('filter_level', opts.level))
    url = opts.url+'/annotation/sequence/'+opts.id+'?'+urlencode(params, True)
    
    # output data
    stdout_from_url(url, auth=token)
    
    return 0
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))
