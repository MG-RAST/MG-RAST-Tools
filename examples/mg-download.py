#!/usr/bin/env python

import os
import sys
import json
import base64
import urllib2
from operator import itemgetter
from optparse import OptionParser
from prettytable import PrettyTable

prehelp = """
NAME
    mg-download

VERSION
    1

SYNOPSIS
    mg-download [ --help, --token <MG-RAST token>, --project <project id>, --metagenome <metagenome id>, --file <file id> --dir <directory name> --list <list files for given id>]

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
    Jared Bischof, Travis Harrison, Folker Meyer, Tobias Paczian, Andreas Wilke
"""

API_URL = "http://api.metagenomics.anl.gov"

# return python struct from JSON output of MG-RAST API
def obj_from_url(url, auth=None, data=None, debug=False, method=None):
    header = {'Accept': 'application/json'}
    if auth:
        header['Auth'] = auth
    if data or method:
        header['Content-Type'] = 'application/json'
    if debug:
        if data:
            print "data:\t"+data
        print "header:\t"+json.dumps(header)
        print "url:\t"+url
    try:
        req = urllib2.Request(url, data, headers=header)
        if method:
            req.get_method = lambda: method
        res = urllib2.urlopen(req)
    except urllib2.HTTPError, error:
        if debug:
            sys.stderr.write("URL: %s\n" %url)
        try:
            eobj = json.loads(error.read())
            sys.stderr.write("ERROR (%s): %s\n" %(error.code, eobj['ERROR']))
        except:
            sys.stderr.write("ERROR (%s): %s\n" %(error.code, error.read()))
        finally:
            sys.exit(1)
    if not res:
        if debug:
            sys.stderr.write("URL: %s\n" %url)
        sys.stderr.write("ERROR: no results returned\n")
        sys.exit(1)
    obj = json.loads(res.read())
    if obj is None:
        if debug:
            sys.stderr.write("URL: %s\n" %url)
        sys.stderr.write("ERROR: return structure not valid json format\n")
        sys.exit(1)
    if len(obj.keys()) == 0:
        if debug:
            sys.stderr.write("URL: %s\n" %url)
        sys.stderr.write("ERROR: no data available\n")
        sys.exit(1)
    if 'ERROR' in obj:
        if debug:
            sys.stderr.write("URL: %s\n" %url)
        sys.stderr.write("ERROR: %s\n" %obj['ERROR'])
        sys.exit(1)
    return obj

# print to file results of MG-RAST or Shock API
def file_from_url(url, handle, auth=None, sauth=None, data=None, debug=False):
    header = {'Accept': 'text/plain'}
    if auth:
        header['Auth'] = auth
    if sauth:
        header['Authorization'] = sauth
    if data:
        header['Content-Type'] = 'application/json'
    if debug:
        if data:
            print "data:\t"+data
        print "header:\t"+json.dumps(header)
        print "url:\t"+url
    try:
        req = urllib2.Request(url, data, headers=header)
        res = urllib2.urlopen(req)
    except urllib2.HTTPError, error:
        try:
            eobj = json.loads(error.read())
            if 'ERROR' in eobj:
                sys.stderr.write("ERROR (%s): %s\n" %(error.code, eobj['ERROR']))
            elif 'error' in eobj:
                sys.stderr.write("ERROR (%s): %s\n" %(error.code, eobj['error'][0]))
            sys.exit(1)
        except:
            sys.stderr.write("ERROR (%s): %s\n" %(error.code, error.read()))
            sys.exit(1)
    if not res:
        sys.stderr.write("ERROR: no results returned\n")
        sys.exit(1)
    while True:
        chunk = res.read(8192)
        if not chunk:
            break
        handle.write(chunk)

# download a file
def file_download(auth, info, dirpath="."):
    fhandle = open(os.path.join(dirpath, info['file_name']), 'w')
    sys.stdout.write("Downloading %s for %s ... "%(info['file_name'], info['id']))
    file_from_url(info['url'], fhandle, auth=auth)
    fhandle.close()
    sys.stdout.write("Done\n")

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp, epilog=posthelp)
    parser.add_option("", "--url", dest="url", default=API_URL, help="MG-RAST API url")
    parser.add_option("", "--token", dest="token", default=None, help="MG-RAST token")
    parser.add_option("", "--project", dest="project", default=None, help="project ID")
    parser.add_option("", "--metagenome", dest="metagenome", default=None, help="metagenome ID")
    parser.add_option("", "--file", dest="file", default=None, help="file ID for given project or metagenome")
    parser.add_option("", "--dir", dest="dir", default=".", help="directory to do downloads")
    parser.add_option("", "--list", dest="list", action="store_true", default=False, help="list files and their info for given ID")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if not (opts.project or opts.metagenome):
        sys.stderr.write("ERROR: a project or metagenome id is required\n")
        return 1
    if not os.path.isdir(opts.dir):
        sys.stderr.write("ERROR: dir '%s' does not exist\n"%opts.dir)
        return 1
    downdir = opts.dir
    
    # get metagenome list
    mgs = []
    if opts.project:
        url  = opts.url+'/project/'+opts.project+'?verbosity=full'
        data = obj_from_url(url, auth=opts.token)
        for mg in data['metagenomes']:
            mgs.append(mg[0])
    elif opts.metagenome:
        mgs.append(opts.metagenome)
    
    # get file lists
    all_files = {}
    for mg in mgs:
        url  = opts.url+'/download/'+mg
        data = obj_from_url(url, auth=opts.token)
        all_files[mg] = data['data']
    
    # just list
    if opts.list:
        pt = PrettyTable(["Metagenome", "File Name", "File ID", "Checksum", "Byte Size"])
        for mg, files in all_files.iteritems():
            for f in files:
                fsize = f['file_size'] if f['file_size'] else 0
                pt.add_row([mg, f['file_name'], f['file_id'], f['file_md5'], fsize])
        pt.align = "l"
        pt.align['Byte Size'] = "r"
        print pt
        return 0
    
    # download all in dirs by ID
    if opts.project:
        downdir = os.path.join(downdir, opts.project)
        if not os.path.isdir(downdir):
            os.mkdir(downdir)
    for mg, files in all_files.iteritems():
        mgdir = os.path.join(downdir, mg)
        if not os.path.isdir(mgdir):
            os.mkdir(mgdir)
        for f in files:
            if opts.file:
                if f['file_id'] == opts.file:
                    file_download(opts.token, f, dirpath=mgdir)
                elif f['file_name'] == opts.file:
                    file_download(opts.token, f, dirpath=mgdir)
            else:
                file_download(opts.token, f, dirpath=mgdir)
    
    return 0


if __name__ == "__main__":
    sys.exit( main(sys.argv) )
