#!/usr/bin/env python

import os
import sys
import json
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-biom-merge

VERSION
    %s

SYNOPSIS
    mg-biom-merge [ --help ] biom1 biom2 [ biom3 biom4 ... ]

DESCRIPTION
    Tool to merge two or more BIOM format files
"""

posthelp = """
Input
    Two or more BIOM files

Output
    Merged BIOM to stdout

EXAMPLES
    mg-biom-merge --help

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)

    # get inputs
    (opts, args) = parser.parse_args()
    if len(args) < 2:
        sys.stderr.write("ERROR: must have at least 2 file inputs\n")
        return 1
    for f in args:
        if not os.path.isfile(f):
            sys.stderr.write("ERROR: %s is not a valid file\n")
    	    return 1
    # get first
    try:
        biom = json.load(open(args[0], 'r'))
    except:
        sys.stderr.write("ERROR: %s BIOM data not correct format\n"%args[0])
        return 1
    
    # merge rest
    for f in args[1:]:
        try:
            b = json.load(open(f, 'r'))
        except:
            sys.stderr.write("ERROR: %s BIOM data not correct format\n"%f)
    	    return 1
    	biom = merge_biom(biom, b)
    
    safe_print(json.dumps(biom)+"\n")
    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
