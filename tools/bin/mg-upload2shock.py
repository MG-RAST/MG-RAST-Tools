#!/usr/bin/env python

import sys
import shock
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-upload2shock

VERSION
    %s

SYNOPSIS
    mg-upload2shock [ --help, --user <user> --passwd <password> --token <auth_token> ] shock_url file_path

DESCRIPTION
    Upload a file to Shock.
"""

posthelp = """
Output
    Shock node ID.

EXAMPLES
    mg-upload2shock --help

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")

    # get inputs
    (opts, args) = parser.parse_args()
    if len(args) != 2:
        sys.stderr.write("ERROR: must have 2 input arguments, shock_url and file_path\n")
        return 1

    # get auth
    token = get_auth_token(opts)
    if token == None:
        sys.stderr.write("ERROR: no token found in KB_AUTH_TOKEN environment variable or input option\n")
        return 1

    shock_url = args[0]
    file_path = args[1]
    shock_client = shock.Client(shock_url, token)

    attributes = {}
    attributes['type'] = 'temp'
    node = shock_client.upload(attr=json.dumps(attributes), data=file_path)
    print json.dumps(node)

    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
