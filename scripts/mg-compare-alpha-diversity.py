#!/usr/bin/env python

import sys
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-compare-alpha-diversity

VERSION
    %s

SYNOPSIS
    mg-compare-alpha-diversity [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --ids <metagenome ids>, --level <taxon level>, --source <datasource> ]

DESCRIPTION
    Calculate alpha diversity for multiple metagenomes.
"""

posthelp = """
Output
    Tab-delimited list of metagenome IDs and their alpha diversity scores.

EXAMPLES
    mg-compare-alpha-diversity --ids "mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3" --level class --source RefSeq

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
    
    # get inputs
    (opts, args) = parser.parse_args()
    if not opts.ids:
        sys.stderr.write("ERROR: one or more ids required\n")
        return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # build url / retrieve data / output data
    id_list = opts.ids.split(',')
    params  = [ ('level', opts.level), ('source', opts.source) ]
    for i in id_list:
        url  = opts.url+'/compute/alphadiversity/'+i+'?'+urlencode(params, True)
        data = obj_from_url(url, auth=token)
        safe_print("%s\t%s\n" %(i, data['data']))
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
