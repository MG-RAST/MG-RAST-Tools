#!/usr/bin/env python

import os
import sys
import json
import time
import pprint
import base64
import getpass
from operator import itemgetter
from optparse import OptionParser
from prettytable import PrettyTable
from mglib import *

prehelp = """
NAME
    mg-project

VERSION
    %s

SYNOPSIS
    mg-project
        --help
        get-info <project ID> 
        get-metadata <project ID>
        upload-metadata <project ID> [--file <filename>]
        make-public <project ID>
        submit-ebi <project ID>

DESCRIPTION
    MG-RAST project tool
    
    supported metadata files: .xls, .xlsx
"""

posthelp = """
Output
    - project info: JSON format
    - project metadata: Excel format

EXAMPLES
    mg-project get-info mgp128

SEE ALSO
    -

AUTHORS
    %s
"""

synch_pause = 900
mgrast_auth = {}
valid_actions = ["get-info", "get-metadata", "update-metadata", "make-public", "submit-ebi"]


def main(args):
    global mgrast_auth, API_URL, SHOCK_URL
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    # access options
    parser.add_option("-u", "--mgrast_url", dest="mgrast_url", default=API_URL, help="MG-RAST API url")
    parser.add_option("-s", "--shock_url", dest="shock_url", default=SHOCK_URL, help="Shock API url")
    parser.add_option("-t", "--token", dest="token", default=None, help="MG-RAST token")
    # other options
    parser.add_option("-f", "--file", dest="mdfile", default=None, help="metadata .xlsx file")
    parser.add_option("", "--debug", dest="debug", action="store_true", default=False, help="Run in debug mode")
    
    # get inputs
    (opts, args) = parser.parse_args()
    API_URL = opts.mgrast_url
    SHOCK_URL = opts.shock_url
    
    # validate inputs
    if len(args) < 1:
        sys.stderr.write("ERROR: missing action\n")
        return 1
    action = args[0]
    if action not in valid_actions:
        sys.stderr.write("ERROR: invalid action. use one of: %s\n"%", ".join(valid_actions))
        return 1
    if len(args) < 2:
        sys.stderr.write("ERROR: missing Project ID\n")
        return 1
    pid = args[1]
    
    # get token
    token = get_auth_token(opts)
    if not token:
        token = raw_input('Enter your MG-RAST auth token: ')
    
    # actions
    if action == "get-info":
        data = obj_from_url(opts.url+'/project/'+pid+'?verbosity=full', auth=token)
        print json.dumps(data, sort_keys=True, indent=4)
    elif action == "get-metadata":
        data = obj_from_url(opts.url+'/metadata/export/'+pid, auth=token)
        print json.dumps(data, sort_keys=True, indent=4)
    elif action == "update-metadata":
        result = post_file(opts.url+'/metadata/update', opts.mdfile, auth=token, data={'project': pid})
        print json.dumps(data, sort_keys=True, indent=4)
    elif action == "make-public":
        data = obj_from_url(opts.url+'/project/'+pid+'/makepublic', auth=token)
        print json.dumps(data, sort_keys=True, indent=4)
    elif action == "submit-ebi":
        data = obj_from_url(opts.url+'/project/'+pid+'/submittoebi', auth=token, method='POST')
        print json.dumps(data, sort_keys=True, indent=4)
    
    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )

