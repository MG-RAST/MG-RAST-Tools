#!/usr/bin/env python

import sys
from operator import itemgetter
from optparse import OptionParser
from mglib import get_auth_token, obj_from_url

prehelp = """
NAME
    mg-abundant-functions

VERSION
    %s

SYNOPSIS
    mg-abundant-functions [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --id <metagenome id>, --level <functional level>, --source <datasource>, --filter_name <function name>, --filter_level <function level>, --top <N lines to return>, --evalue <evalue negative exponent>, --identity <percent identity>, --length <alignment length> ]

DESCRIPTION
    Retrieve top abundant functions for metagenome.
"""

posthelp = """
Output
    Tab-delimited list of function and abundance sorted by abundance (largest first). 'top' option controls number of rows returned.

EXAMPLES
    mg-abundant-functions --id "mgm4750361.3" --level level3 --source SubSystems --top 20 --evalue 8

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
    parser.add_option("", "--level", dest="level", default='function', help="functional level to retrieve abundances for, default is function")
    parser.add_option("", "--source", dest="source", default='Subsystems', help="datasource to filter results by, default is Subsystems")
    parser.add_option("", "--filter_name", dest="filter_name", default=None, help="function name to filter by")
    parser.add_option("", "--filter_level", dest="filter_level", default=None, help="function level to filter by")
    parser.add_option("", "--top", dest="top", type="int", default=10, help="display only the top N taxa, default is 10")
    parser.add_option("", "--evalue", dest="evalue", type="int", default=5, help="negative exponent value for maximum e-value cutoff, default is 5")
    parser.add_option("", "--identity", dest="identity", type="int", default=60, help="percent value for minimum % identity cutoff, default is 60")
    parser.add_option("", "--length", dest="length", type="int", default=15, help="value for minimum alignment length cutoff, default is 15")
    parser.add_option("", "--version", type="int", dest="version", default=1, help="M5NR annotation version to use, default is 1")
    
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
    params = [ ('id', opts.id),
               ('group_level', opts.level), 
               ('source', opts.source),
               ('evalue', opts.evalue),
               ('identity', opts.identity),
               ('length', opts.length),
               ('version', opts.version),
               ('result_type', 'abundance'),
               ('asynchronous', '1'),
               ('hide_metadata', '1') ]
    url = opts.url+'/matrix/function?'+urlencode(params, True)
    
    # retrieve data
    top_ann = {}
    biom = async_rest_api(url, auth=token)
    
    # get sub annotations
    sub_ann = set()
    if opts.filter_name and opts.filter_level:
        params = [ ('filter', opts.filter_name),
                   ('filter_level', opts.filter_level),
                   ('min_level', opts.level),
                   ('version', opts.version),
                   ('source', opts.source) ]
        url = opts.url+'/m5nr/ontology?'+urlencode(params, True)
        data = obj_from_url(url)
        level = 'level4' if opts.level == 'function' else opts.level
        sub_ann = set( map(lambda x: x[level], data['data']) )
    
    # sort data
    if biom["matrix_type"] == "sparse":
        for d in sorted(biom['data'], key=itemgetter(2), reverse=True):
            name = biom['rows'][d[0]]['id']  # if opts.source != 'Subsystems' else biom['rows'][d[0]]['metadata']['ontology'][-1]
            if len(top_ann) >= opts.top:
                break
            if sub_ann and (name not in sub_ann):
                continue
            top_ann[name] = d[2]
    if biom["matrix_type"] == "dense":
        sortindex = sorted(range(len(biom['data'])), key=biom['data'].__getitem__, reverse=True)
        for n in sortindex:
            name = biom['rows'][n]['id'] # if opts.source != 'Subsystems' else biom['rows'][n]['metadata']['ontology'][-1]
            if len(top_ann) >= opts.top:
                break
            if sub_ann and (name not in sub_ann):
                continue
            top_ann[name] = biom['data'][n][0]

    # output data
    for k, v in sorted(top_ann.items(), key=itemgetter(1), reverse=True):
        safe_print("%s\t%d\n" %(k, v))
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
