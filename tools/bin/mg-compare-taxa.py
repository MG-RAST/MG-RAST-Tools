#!/usr/bin/env python

import sys
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-compare-taxa

VERSION
    %s

SYNOPSIS
    mg-compare-taxa [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --ids <metagenome ids>, --level <taxon level>, --source <datasource>, --filter_name <taxon name>, --filter_level <taxon level>, --evalue <evalue negative exponent>, --identity <percent identity>, --length <alignment length>, --format <cv: 'text' or 'biom'> ]

DESCRIPTION
    Retrieve matrix of taxanomic abundance profiles for multiple metagenomes.
"""

posthelp = """
Output
    1. Tab-delimited table of taxanomic abundance profiles, metagenomes in columns and taxa in rows.
    2. BIOM format of taxanomic abundance profiles.

EXAMPLES
    mg-compare-taxa --ids "kb|mg.286,kb|mg.287,kb|mg.288,kb|mg.289" --level class --source RefSeq --format text --evalue 8

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
    parser.add_option("", "--filter_name", dest="filter_name", default=None, help="taxon name to filter by")
    parser.add_option("", "--filter_level", dest="filter_level", default=None, help="taxon level to filter by")
    parser.add_option("", "--format", dest="format", default='text', help="output format: 'text' for tabbed table, 'biom' for BIOM format, default is text")
    parser.add_option("", "--evalue", dest="evalue", default=5, help="negative exponent value for maximum e-value cutoff, default is 5")
    parser.add_option("", "--identity", dest="identity", default=60, help="percent value for minimum % identity cutoff, default is 60")
    parser.add_option("", "--length", dest="length", default=15, help="value for minimum alignment length cutoff, default is 15")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if not opts.ids:
        sys.stderr.write("ERROR: one or more ids required\n")
        return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # build url
    id_list = kbids_to_mgids( opts.ids.split(',') )
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
    url = opts.url+'/matrix/organism?'+urllib.urlencode(params, True)

    # retrieve data
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
    
    # output data
    if opts.format == 'biom':
        safe_print(json.dumps(biom)+"\n")
    elif opts.format == 'text':
        biom_to_tab(biom, sys.stdout, rows=sub_ann)
    else:
        sys.stderr.write("ERROR: invalid format type, use one of: text, biom\n")
        return 1
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
