#!/usr/bin/env python

import sys
import os
import json
import yaml
import shutil
import hashlib
from optparse import OptionParser
from prettytable import PrettyTable
from mglib import VERSION, get_auth_token, AUTH_LIST, API_URL, obj_from_url, file_from_url, random_str

VERSION = 'alpha'

prehelp = """
NAME
    mg-export-research-object

VERSION
    %s

SYNOPSIS
    mg-export-research-object [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --metagenome <metagenome id>, --dir <directory name> --list <list manifest>]

DESCRIPTION
    Retrieve metagenome research object.
    Note: This is an alpha version and currently does not produce a full Research Object.
"""

posthelp = """
Output
    List available files in manifest.
      OR
    Download research object from manifest.

EXAMPLES
    mg-export-research-object --metagenome mgm4441680.3 --list

SEE ALSO
    -

AUTHORS
    %s
"""

def my_unicode_repr(self, data):
    return self.represent_str(data.encode('utf-8'))

def edit_input(text, mg):
    info = yaml.load(text)
    param = mg['pipeline_parameters']
    info['jobid'] = int(mg['job_id'])
    info['sequences']['path'] = "../data/"+mg['id']+".050.upload."+param['file_type']
    if 'filterLn' in info:
        info['filterLn'] = True if param['filter_ln'] == "yes" else False
    if 'filterAmbig' in info:
        info['filterAmbig'] = True if param['filter_ambig'] == "yes" else False
    if 'deviation' in info:
        info['deviation'] = float(param['filter_ln_mult'])
    if 'maxAmbig' in info:
        info['maxAmbig'] = int(param['max_ambig'])
    if 'derepPrefix' in info:
        if param['dereplicate'] == 'yes':
            info['derepPrefix'] = int(param['prefix_length'])
        else:
            info['derepPrefix'] = 0
    if 'minQual' in info:
        info['minQual'] = int(param['min_qual'])
    if 'maxLqb' in info:
        info['maxLqb'] = int(param['max_lqb'])
    
    yaml.representer.Representer.add_representer(unicode, my_unicode_repr)
    return yaml.dump(info, allow_unicode=True, default_flow_style=False)

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--url", dest="url", default=API_URL, help="MG-RAST API url")
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")
    parser.add_option("", "--metagenome", dest="metagenome", default=None, help="metagenome ID")
    parser.add_option("", "--dir", dest="dir", default=".", help="directory to export to")
    parser.add_option("", "--list", dest="list", action="store_true", default=False, help="list files in manifest")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if not opts.metagenome:
        sys.stderr.write("ERROR: a metagenome id is required\n")
        return 1
    if not os.path.isdir(opts.dir):
        sys.stderr.write("ERROR: dir '%s' does not exist\n"%opts.dir)
        return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # get mg info
    url = opts.url+'/metagenome/'+opts.metagenome
    mg  = obj_from_url(url, auth=token)
    
    # get manifest
    url  = opts.url+'/researchobject/manifest/'+opts.metagenome
    data = obj_from_url(url, auth=token)
    
    # just list
    if opts.list:
        pt = PrettyTable(["File Name", "Folder", "Media Type"])
        for info in data["aggregates"]:
            pt.add_row([info["bundledAs"]["filename"], info["bundledAs"]["folder"], info["mediatype"]])
        pt.align = "l"
        print(pt)
        return 0
    
    # get cwl files
    temp_name = random_str(10)
    pipeline_dir = os.path.join(opts.dir, temp_name)
    git_clone = "git clone https://github.com/MG-RAST/pipeline.git " + pipeline_dir
    os.system(git_clone)
    
    # download manifest
    sha1s = []
    base = data["@context"][0]["@base"].strip('/')
    manifest_dir = os.path.join(opts.dir, base)
    os.mkdir(manifest_dir)
    data_str = json.dumps(data)
    open(os.path.join(manifest_dir, data["manifest"]), 'w').write(data_str)
    sha1s.append([ hashlib.sha1(data_str).hexdigest(), os.path.join(base, data["manifest"]) ])
    
    # download aggregates
    for info in data["aggregates"]:
        sys.stdout.write("Downloading %s ... "%(info["bundledAs"]["filename"]))
        folder = info["bundledAs"]["folder"].strip('/')
        folder_dir = os.path.join(opts.dir, folder)
        if not os.path.isdir(folder_dir):
            os.mkdir(folder_dir)
        if "githubusercontent" in info["uri"]:
            pos = info["uri"].find("CWL")
            src = os.path.join(pipeline_dir, info["uri"][pos:])
            dst = os.path.join(folder_dir, info["bundledAs"]["filename"])
            text = open(src, 'r').read().replace('../Inputs/', '').replace('../Tools/', '').replace('../Workflows/', '')
            if dst.endswith('job.yaml'):
                text = edit_input(text, mg) 
            open(dst, 'w').write(text)
            sha1s.append([ hashlib.sha1(text).hexdigest(), os.path.join(folder, info["bundledAs"]["filename"]) ])
        else:
            fh = open(os.path.join(folder_dir, info["bundledAs"]["filename"]), 'w')
            s1 = file_from_url(info["uri"], fh, auth=token, sha1=True)
            fh.close()
            sha1s.append([ s1, os.path.join(folder, info["bundledAs"]["filename"]) ])
        sys.stdout.write("Done\n")
    
    # output sha1
    mansha1 = open(os.path.join(opts.dir, "manifest-sha1.txt"), 'w')
    tagsha1 = open(os.path.join(opts.dir, "tagmanifest-sha1.txt"), 'w')
    sha1s.sort(key=lambda x: x[1])
    for s1 in sha1s:
        if s1[1].startswith('data'):
            mansha1.write("%s\t%s\n"%(s1[0], s1[1]))
        else:
            tagsha1.write("%s\t%s\n"%(s1[0], s1[1]))
    mansha1.close()
    tagsha1.close()
    
    # cleanup
    shutil.rmtree(pipeline_dir)
    
    return 0


if __name__ == "__main__":
    sys.exit( main(sys.argv) )
