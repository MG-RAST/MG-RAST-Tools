#!/usr/bin/env python

import sys
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-compare-functions

VERSION
    %s

SYNOPSIS
    mg-compare-functions [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --ids <metagenome ids>, --level <functional level>, --source <datasource>, --evalue <evalue negative exponent>, --identity <percent identity>, --length <alignment length>, --format <cv: 'text' or 'biom'> ]

DESCRIPTION
    Retrieve matrix of functional abundance profiles for multiple metagenomes.
"""

posthelp = """
Output
    1. Tab-delimited table of functional abundance profiles, metagenomes in columns and functions in rows.
    2. BIOM format of functional abundance profiles.

EXAMPLES
    mg-compare-functions --ids "kb|mg.286,kb|mg.287,kb|mg.288,kb|mg.289" --level level2 --source KO --format text --evalue 8

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
    parser.add_option("", "--level", dest="level", default='function', help="functional level to retrieve abundances for, default is function")
    parser.add_option("", "--source", dest="source", default='Subsystems', help="datasource to filter results by, default is Subsystems")
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
    url = opts.url+'/matrix/function?'+urllib.urlencode(params, True)

    # retrieve data
    biom = async_rest_api(url, auth=token)
    
    # output data
    if opts.format == 'biom':
        sys.stdout.write(json.dumps(biom)+"\n")
    elif opts.format == 'text':
        biom_to_tab(biom, sys.stdout)
    else:
        sys.stderr.write("ERROR: invalid format type, use one of: text, biom\n")
        return 1
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
