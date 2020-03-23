#!/usr/bin/env python

import sys
from operator import itemgetter
from argparse import ArgumentParser
from mglib import get_auth_token, obj_from_url, async_rest_api, AUTH_LIST, sparse_to_dense, safe_print, API_URL, VERSION, urlencode

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
    mg-abundant-taxa --id "mgm4750361.3" --level genus --source RefSeq --top 20 --evalue 8

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_argument("--id", dest="id", default=None, help="KBase Metagenome ID")
    parser.add_argument("--url", dest="url", default=API_URL, help="communities API url")
    parser.add_argument("--user", dest="user", default=None, help="OAuth username")
    parser.add_argument("--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_argument("--token", dest="token", default=None, help="OAuth token")
    parser.add_argument("--level", dest="level", default='species', help="taxon level to retrieve abundances for, default is species")
    parser.add_argument("--source", dest="source", default='SEED', help="datasource to filter results by, default is SEED")
    parser.add_argument("--filter_name", dest="filter_name", default=None, help="taxon name to filter by")
    parser.add_argument("--filter_level", dest="filter_level", default=None, help="taxon level to filter by")
    parser.add_argument("--top", dest="top", type=int, default=10, help="display only the top N taxa, default is 10")
    parser.add_argument("--evalue", dest="evalue", type=int, default=5, help="negative exponent value for maximum e-value cutoff, default is 5")
    parser.add_argument("--identity", dest="identity", type=int, default=60, help="percent value for minimum %% identity cutoff, default is 60")
    parser.add_argument("--length", dest="length", type=int, default=15, help="value for minimum alignment length cutoff, default is 15")
    parser.add_argument("--version", type=int, dest="version", default=1, help="M5NR annotation version to use, default is 1")
    
    # get inputs
    opts = parser.parse_args()
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
    params = [('id', opts.id),
              ('group_level', opts.level),
              ('source', opts.source),
              ('evalue', opts.evalue),
              ('identity', opts.identity),
              ('length', opts.length),
              ('version', opts.version),
              ('result_type', 'abundance'),
              ('asynchronous', '1'),
              ('hide_metadata', '1')]
    url = opts.url+'/matrix/organism?'+urlencode(params, True)

    # retrieve data
    top_ann = {}
    biom = async_rest_api(url, auth=token)
    
    # get sub annotations
    sub_ann = set()
    if opts.filter_name and opts.filter_level:
        params = [('filter', opts.filter_name),
                  ('filter_level', opts.filter_level),
                  ('min_level', opts.level),
                  ('version', opts.version)]
        url = opts.url+'/m5nr/taxonomy?'+urlencode(params, True)
        data = obj_from_url(url)
        sub_ann = set(map(lambda x: x[opts.level], data['data']))
    biomorig = biom
    biom = biomorig["data"]
    if biom['matrix_type'] == "dense":
        data = biom['data']
    else:
        data = sparse_to_dense(biom['data'], len(biom['rows']), len(biom['cols']))
    rows = [biom['rows'][i]['id'] for i in range(len(biom['rows']))]
    datalist = [biom['data'][i][0] for i in range(len(biom['rows']))]
    data2 = zip(rows, datalist)
    # sort data
    for d in sorted(data2, key=itemgetter(1), reverse=True):
        name = d[0]
        if len(top_ann) >= opts.top:
            break
        if sub_ann and (name not in sub_ann):
            continue
        top_ann[name] = d[1]

    # output data
    for k, v in sorted(top_ann.items(), key=itemgetter(1), reverse=True):
        safe_print("%s\t%d\n" %(k, v))
    
    return 0
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))
