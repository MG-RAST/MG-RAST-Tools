#!/usr/bin/env python

import sys
import json
from argparse import ArgumentParser
from mglib import get_auth_token, post_file, obj_from_url, VERSION, AUTH_LIST, API_URL

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
        status-ebi <project ID>

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
valid_actions = ["get-info", "get-metadata", "update-metadata", "make-public", "submit-ebi", "status-ebi"]


def main(args):
    global API_URL
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    # access options
    parser.add_argument("-u", "--url", dest="url", default=API_URL, help="MG-RAST API url")
    parser.add_argument("-t", "--token", dest="token", default=None, help="MG-RAST token")
    # other options
    parser.add_argument("-f", "--file", dest="mdfile", default=None, help="metadata .xlsx file")
    parser.add_argument("--taxa", dest="taxa", default=None, help="metagenome_taxonomy for project: http://www.ebi.ac.uk/ena/data/view/Taxon:408169")
    parser.add_argument("--debug", dest="debug", action="store_true", default=False, help="Run in debug mode")
    parser.add_argument("args",type=str, nargs="+", help="Action (" + ",".join(valid_actions)+")" )
    
    # get inputs
    opts = parser.parse_args()
    args = opts.args
    API_URL = opts.url
    
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
        data = obj_from_url(opts.url+'/project/'+pid+'?verbosity=full&nocache=1', auth=token)
        print(json.dumps(data, sort_keys=True, indent=4))
    elif action == "get-metadata":
        data = obj_from_url(opts.url+'/metadata/export/'+pid, auth=token)
        print(json.dumps(data, sort_keys=True, indent=4))
    elif action == "update-metadata":
        result = post_file(opts.url+'/metadata/update', 'upload', opts.mdfile, auth=token, data=json.dumps({'project': pid}, separators=(',',':')))
        print(json.dumps(data, sort_keys=True, indent=4))
    elif action == "make-public":
        data = obj_from_url(opts.url+'/project/'+pid+'/makepublic', auth=token)
        print(json.dumps(data, sort_keys=True, indent=4))
    elif action == "submit-ebi":
        debug = 1 if opts.debug else 0
        info  = {
            'project_id': pid,
            'debug': debug
        }
        if opts.taxa:
            info['metagenome_taxonomy'] = {}
            proj = obj_from_url(opts.url+'/project/'+pid+'?verbosity=verbose&nocache=1', auth=token)
            for mg in proj['metagenomes']:
                info['metagenome_taxonomy'][mg['metagenome_id']] = opts.taxa
        data = obj_from_url(opts.url+'/submission/ebi', auth=token, data=json.dumps(info, separators=(',',':')))
        print(json.dumps(data, sort_keys=True, indent=4))
    elif action == "status-ebi":
        data = obj_from_url(opts.url+'/submission/'+pid, auth=token)
        print(json.dumps(data, sort_keys=True, indent=4))
    
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

