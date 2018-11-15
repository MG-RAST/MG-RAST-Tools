#!/usr/bin/env python

import sys
import os
from argparse import ArgumentParser
from prettytable import PrettyTable
from mglib import VERSION, get_auth_token, AUTH_LIST, API_URL, obj_from_url, file_from_url

prehelp = """
NAME
    mg-download

VERSION
    %s

SYNOPSIS
    mg-download [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --project <project id>, --metagenome <metagenome id>, --file <file id> --dir <directory name> --list <list files for given id>]

DESCRIPTION
    Retrieve metadata for a metagenome.
"""

posthelp = """
Output
    List available files (name and size) for given project or metagenome id.
      OR
    Download of file(s) for given project, metagenome, or file id.

EXAMPLES
    mg-download --metagenome mgm4441680.3 --list

SEE ALSO
    -

AUTHORS
    %s
"""

# download a file
def file_download(auth, info, dirpath="."):
    fhandle = open(os.path.join(dirpath, info['file_name']), 'w')
    sys.stdout.write("Downloading %s for %s ... "%(info['file_name'], info['id']))
    file_from_url(info['url'], fhandle, auth=auth)
    fhandle.close()
    sys.stdout.write("Done\n")

def main(args):
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_argument("--url", dest="url", default=API_URL, help="communities API url")
    parser.add_argument("--user", dest="user", default=None, help="OAuth username")
    parser.add_argument("--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_argument("--token", dest="token", default=None, help="OAuth token")
    parser.add_argument("--project", dest="project", default=None, help="project ID")
    parser.add_argument("--metagenome", dest="metagenome", default=None, help="metagenome ID")
    parser.add_argument("--file", dest="file", default=None, help="file ID for given project or metagenome")
    parser.add_argument("--dir", dest="dir", default=".", help="directory to do downloads")
    parser.add_argument("--list", dest="list", action="store_true", default=False, help="list files and their info for given ID")
    
    # get inputs
    opts = parser.parse_args()
    if not (opts.project or opts.metagenome):
        sys.stderr.write("ERROR: a project or metagenome id is required\n")
        return 1
    if not os.path.isdir(opts.dir):
        sys.stderr.write("ERROR: dir '%s' does not exist\n"%opts.dir)
        return 1
    downdir = opts.dir
    
    # get auth
    token = get_auth_token(opts)
    
    # get metagenome list
    mgs = []
    if opts.project:
        url  = opts.url+'/project/'+opts.project+'?verbosity=full'
        data = obj_from_url(url, auth=token)
        for mg in data['metagenomes']:
            mgs.append(mg["metagenome_id"])
    elif opts.metagenome:
        mgs.append(opts.metagenome)
    
    # get file lists
    all_files = {}
    for mg in mgs:
        url  = opts.url+'/download/'+mg
        data = obj_from_url(url, auth=token)
        all_files[mg] = data['data']
    
    # just list
    if opts.list:
        pt = PrettyTable(["Metagenome", "File Name", "File ID", "Checksum", "Byte Size"])
        for mg, files in all_files.items():
            for f in files:
                fsize = f['file_size'] if f['file_size'] else 0
                pt.add_row([mg, f['file_name'], f['file_id'], f['file_md5'], fsize])
        pt.align = "l"
        pt.align['Byte Size'] = "r"
        print(pt)
        return 0
    
    # download all in dirs by ID
    if opts.project:
        downdir = os.path.join(downdir, opts.project)
        if not os.path.isdir(downdir):
            os.mkdir(downdir)
    for mg, files in all_files.items():
        mgdir = os.path.join(downdir, mg)
        if not os.path.isdir(mgdir):
            os.mkdir(mgdir)
        for f in files:
            if opts.file:
                if f['file_id'] == opts.file:
                    file_download(token, f, dirpath=mgdir)
                elif f['file_name'] == opts.file:
                    file_download(token, f, dirpath=mgdir)
            else:
                file_download(token, f, dirpath=mgdir)
    
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
