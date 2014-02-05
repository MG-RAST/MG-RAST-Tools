#!/usr/bin/env python

import sys
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-upload2ws

VERSION
    %s

SYNOPSIS
    mg-upload2ws [ --help, --id <refrence ID>, --type <ID type>, --workspace <workspace name>, --name <object name> ]

DESCRIPTION
    Upload data to the workspace.
"""

posthelp = """
Output
    Workspace object.

EXAMPLES
    mg-upload2ws --help

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--id", dest="id", default=None, help="ID to add to workspace")
    parser.add_option("", "--type", dest="type", default=None, help="type of ID: one of 'metagenome' or 'project'")
    parser.add_option("", "--workspace", dest="workspace", default=None, help="workspace name")
    parser.add_option("", "--name", dest="name", default=None, help="object name")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if not (opts.id and opts.type):
        sys.stderr.write("ERROR: id and id-type required\n")
        return 1
    if not (opts.workspace and opts.name):
        sys.stderr.write("ERROR: workspace and object names required\n")
        return 1
    
    # upload to workspace
    wtype = ''
    wdata = { 'name': opts.name,
              'created': time.strftime("%Y-%m-%d %H:%M:%S"),
              'type': opts.type,
              'ref': {'ID': opts.id, 'URL': "%s/%s/%s"%(API_URL, opts.type, opts.id)} }
    if opts.type == 'metagenome':
        wtype = 'Communities.Metagenome-1.0'
    elif opts.type == 'project':
        wtype = 'Communities.Project-1.0'
    else:
        sys.stderr.write("ERROR: type %s is invalid\n"%opts.type)
        return 1
    load_to_ws(opts.workspace, wtype, opts.name, wdata)
    
    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
