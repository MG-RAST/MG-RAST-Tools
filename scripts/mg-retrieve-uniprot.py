#!/usr/bin/env python

import sys
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib.mglib import *

UNIPROT_URL = "http://www.uniprot.org/uniprot/"

prehelp = """
NAME
    mg-retrieve-uniprot

VERSION
    %s

SYNOPSIS
    mg-retrieve-uniprot [ --help, --md5 <sequence md5>, --id <accession ID>, --source <datasource> ]

DESCRIPTION
    Retrieve the uniprot result for a sequence md5 or accession id.
"""

posthelp = """
Output
    Uniprot output

EXAMPLES
    mg-retrieve-uniprot --md5 ffc62262a18b38671c3e337150ef535f --source SwissProt

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--url", dest="url", default=API_URL, help="API url")
    parser.add_option("", "--md5", dest="md5", default=None, help="sequence md5")
    parser.add_option("", "--id", dest="id", default=None, help="accession ID")
    parser.add_option("", "--source", dest="source", default='SwissProt', help="datasource to get record from, one of: SwissProt, TreMBL, InterPro")
    parser.add_option("", "--version", dest="version", default='1', help="M5NR version to use, one of 1 or 9")
    
    # get inputs
    (opts, args) = parser.parse_args()

    # build url for m5nr query
    params = [ ('limit', '1'),
               ('version', opts.version),
               ('source', opts.source) ]
    if opts.md5:
        url = opts.url+'/m5nr/md5/'+opts.md5+'?'+urllib.urlencode(params, True)
    elif opts.id:
        url = opts.url+'/m5nr/accession/'+opts.id+'?'+urllib.urlencode(params, True)
    else:
        sys.stderr.write("ERROR: no md5 checksum or accession given\n")
        return 1
        
    # retrieve data
    result = obj_from_url(url)
    if len(result['data']) == 0:
        sys.stderr.write("ERROR: no match in M5NR version %s\n"%opts.version)
        return 1
    
    # output data
    stdout_from_url(UNIPROT_URL+result['data'][0]['accession']+'.txt')
    
    return 0
    
if __name__ == "__main__":
    sys.exit( main(sys.argv) )
