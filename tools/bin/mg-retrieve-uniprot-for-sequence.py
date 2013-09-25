#!/usr/bin/env python

import sys
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib import *

UNIPROT_URL = "http://www.uniprot.org/uniprot/"

prehelp = """
NAME
    mg-extract-sequences

VERSION
    %s

SYNOPSIS
    mg-retrieve-uniprot-for-sequence --id <sequence md5>

DESCRIPTION
    Retrieve the uniprot result for a sequence md5.
"""

posthelp = """
Output
    Uniprot output

EXAMPLES
    mg-retrieve-uniprot-for-sequence --md5 41a93070f6a6f75d69c7b83a8a305e7d

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
    
    # get inputs
    (opts, args) = parser.parse_args()
    
    if not opts.md5:
        sys.stderr.write("ERROR: no md5 id given\n")
        sys.exit(1)

    # build url for m5nr query
    url = opts.url+'/m5nr/md5/'+opts.md5+'?source=InterPro'
    retval = obj_from_url(url)

    if not retval['data'][0]:
        sys.stderr.write("ERROR: md5 has no UniProt hits\n")
        sys.exit(1)

    url = UNIPROT_URL+retval['data'][0]['accession']+'.txt'
    
    # output data
    stout_from_url(url)
    
    return 0
    
if __name__ == "__main__":
    sys.exit( main(sys.argv) )
