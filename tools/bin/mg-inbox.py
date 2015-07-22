#!/usr/bin/env python

import os
import sys
import json
import time
import base64
import getpass
from operator import itemgetter
from optparse import OptionParser
from prettytable import PrettyTable
from mglib import *

prehelp = """
NAME
    mg-inbox

VERSION
    %s

SYNOPSIS
    mg-inbox
        --help
        login <login name>
        view all
        view sequence
        upload <file> <file> ... [--gzip, --bzip2]
        rename <file id> <new name>
        validate sequence <seq file id> <seq file id> ...
        validate metadata <excel file id> <excel file id> ...
        compute sff2fastq <sff file id>
        compute demultiplex <seq file id> <barcode file id>
        compute pairjoin <pair1 seq file id> <pair2 seq file id> [--retain, --joinfile <filename>]
        compute pairjoin_demultiplex <pair1 seq file id> <pair2 seq file id> <index file id> [--retain, --joinfile <filename>]
        delete <file id> <file id> ...
        submit <file id> <file id> ... [--project <project id>, --metadata <file id>]

DESCRIPTION
    MG-RAST inbox operations
"""

posthelp = """
Output
    Status of command
      OR
    List contents of inbox 

EXAMPLES
    mg-inbox view all

SEE ALSO
    -

AUTHORS
    %s
"""

auth_file   = os.path.join(os.path.expanduser('~'), ".mgrast_auth")
mgrast_auth = {}
valid_actions    = ["login", "view", "upload", "rename", "validate", "compute", "delete", "submit", "submitall"]
view_options     = ["all", "sequence"]
validate_options = ["sequence", "metadata"]
compute_options  = ["sff2fastq", "demultiplex", "pairjoin", "pairjoin_demultiplex"]

def get_auth(token):
    if token:
        auth_obj = obj_from_url(API_URL+"/user/authenticate", auth=token)
        auth_obj['token'] = token
        return auth_obj
    if not os.path.isfile(auth_file):
        sys.stderr.write("ERROR: missing authentication file, please login\n")
        return None
    auth_obj = json.load(open(auth_file,'r'))
    if ("token" not in auth_obj) and ("id" not in auth_obj) and ("expiration" not in auth_obj):
        sys.stderr.write("ERROR: invalid authentication file, please login\n")
        return None
    if time.time() > int(auth_obj["expiration"]):
        sys.stderr.write("ERROR: expired authentication file, please login\n")
        return None
    return auth_obj

def login(name, password):
    auth_str = "mggo4711"+base64.b64encode(name+":"+password)
    auth_obj = obj_from_url(API_URL+"?verbosity=verbose", auth=auth_str)
    json.dump(auth_obj, open(auth_file,'w'))

def check_id(uuid, inbox):
    if len(inbox['files']) == 0:
        sys.stderr.write("ERROR: File ID '%s' does not exist in your inbox. Did you use File Name by mistake?\n"%uuid)
        sys.exit(1)
    ids = map(lambda x: x['id'], inbox['files'])
    if uuid not in ids:
        sys.stderr.write("ERROR: File ID '%s' does not exist in your inbox. Did you use File Name by mistake?\n"%uuid)
        sys.exit(1)

def view(vtype):
    data = obj_from_url(API_URL+"/inbox", auth=mgrast_auth['token'])
    files = sorted(data['files'], key=itemgetter('timestamp'))
    if vtype == "sequence":
        pt = PrettyTable(["ID", "name", "md5sum", "size", "time", "format", "seq_type", "seq_count", "bp_count", "actions"])
        for f in files:
            if ('data_type' in f) and (f['data_type'] == 'sequence'):
                row = [
                    f['id'],
                    f['filename'],
                    f['checksum'],
                    f['filesize'],
                    f['timestamp'],
                    f['stats_info']['file_type'],
                    f['stats_info']['sequence_type'],
                    f['stats_info']['sequence_count'],
                    f['stats_info']['bp_count'],
                    []
                ]
                if ('actions' in f) and (len(f['actions']) > 0):
                    for a in f['actions']:
                        row[9].append(a['name']+": "+a['status'])
                row[9] = "\n".join(row[9])
                pt.add_row(row)
    else:
        pt = PrettyTable(["ID", "name", "md5sum", "size", "time", "format", "actions"])
        for f in files:
            row = [
                f['id'],
                f['filename'],
                f['checksum'],
                f['filesize'],
                f['timestamp'],
                f['stats_info']['file_type'],
                []
            ]
            if ('actions' in f) and (len(f['actions']) > 0):
                for a in f['actions']:
                    row[6].append(a['name']+": "+a['status'])
            row[6] = "\n".join(row[6])
            pt.add_row(row)
    pt.align = "r"
    pt.align['name'] = "l"
    pt.align['time'] = "l"
    print pt

def upload(fformat, files):
    for f in files:
        attr = json.dumps({
            "type": "inbox",
            "id": mgrast_auth['id'],
            "user": mgrast_auth['login'],
            "email": mgrast_auth['email']
        })
        # POST to shock
        result = post_node(SHOCK_URL+"/node", fformat, f, attr, auth="mgrast "+mgrast_auth['token'])
        # compute file info
        info = obj_from_url(API_URL+"/inbox/info/"+result['id'], auth=mgrast_auth['token'])
        print info['status']
        # compute sequence stats
        if info['stats_info']['file_type'] in ['fasta', 'fastq']:
            stats = obj_from_url(API_URL+"/inbox/stats/"+result['id'], auth=mgrast_auth['token'])
            print info['status'].replace("stats computation", "validation")

def rename(fid, fname):
    data = {"name": fname, "file": fid}
    result = obj_from_url(API_URL+"/inbox/rename", data=json.dumps(data), auth=mgrast_auth['token'])
    print result['status']

def validate(fformat, files, get_info=False):
    for f in files:
        data = obj_from_url(API_URL+"/inbox/"+f, auth=mgrast_auth['token'])
        check_id(f, data)
        ids = map(lambda x: data, data)
        if ('data_type' in data) and (data['data_type'] == fformat):
            print "%s (%s) is a valid %s file"%(data['filename'], f, fformat)
        elif fformat == 'sequence':
            if data['stats_info']['file_type'] in ['fasta', 'fastq']:
                info = obj_from_url(API_URL+"/inbox/stats/"+f, auth=mgrast_auth['token'])
                print info['status'].replace("stats computation", "validation")
            else:
                sys.stderr.write("ERROR: %s (%s) is not a fastq or fasta file\n"%(data['filename'], f))
        elif fformat == 'metadata':
            if data['stats_info']['file_type'] == 'excel':
                info = obj_from_url(API_URL+"/inbox/validate/"+f, auth=mgrast_auth['token'])
                if get_info:
                    return info
                else:
                    print info['status']
                    if info['status'].startswith('invalid'):
                        print info['error']
            else:
                sys.stderr.write("ERROR: %s (%s) is not a spreadsheet file\n"%(data['filename'], f))

def compute(action, files, retain, joinfile):
    if action == "sff2fastq":
        data = {"sff_file": files[0]}
    elif action == "demultiplex":
        data = {"seq_file": files[0], "barcode_file": files[1]}
    elif action == "pairjoin":
        data = {"pair_file_1": files[0], "pair_file_2": files[1], "retain": 1 if retain else 0}
        if joinfile:
            data['output'] = joinfile
    elif action == "pairjoin_demultiplex":
        data = {"pair_file_1": files[0], "pair_file_2": files[1], "index_file": files[2], "retain": 1 if retain else 0}
        if joinfile:
            data['output'] = joinfile
    else:
        sys.stderr.write("ERROR: invalid compute option. use one of: %s\n"%", ".join(compute_options))
    info = obj_from_url(API_URL+"/inbox/"+action, data=json.dumps(data), auth=mgrast_auth['token'])
    print info['status']

def delete(files):
    for f in files:
        result = obj_from_url(API_URL+"/inbox/"+f, auth=mgrast_auth['token'], method='DELETE')
        print result['status']

def submit(files, project, metadata):
    mdata = None
    if metadata:
        # TODO metadata stuff
        minfo = validate('metadata', [metadata], get_info=True)
        if minfo['status'].startswith('invalid') or ('extracted' not in minfo):
            print minfo['error'] if 'error' in minfo else 'ERROR: unable to validate metadata '+metadata
            return
        mdata = obj_from_url(API_URL+"/inbox/"+minfo['extracted'], auth=mgrast_auth['token'])
    info = []
    for f in files:
        x = obj_from_url(API_URL+"/inbox/"+f, auth=mgrast_auth['token'])
        check_id(f, data)
        if ('data_type' in x) and (x['data_type'] == 'sequence'):
            info.append(x)
        else:
            sys.stderr.write("ERROR: %s (%s) is not a valid sequence file\n"%(x['filename'], f))
            sys.exit(1)
    # process sequence files
    mgids = []
    for i in info:
        # reserve job
        data = {"input_id": i['id'], "name": os.path.splitext(i['filename'])[0]}
        rjob = obj_from_url(API_URL+"/job/reserve", data=json.dumps(data), auth=mgrast_auth['token'])
        # create job
        data = {"input_id": i['id'], "metagenome_id": rjob['metagenome_id']}
        obj_from_url(API_URL+"/job/create", data=json.dumps(data), auth=mgrast_auth['token'])
        # add to project
        if project:
            data = {"project_id": project, "metagenome_id": rjob['metagenome_id']}
            obj_from_url(API_URL+"/job/addproject", data=json.dumps(data), auth=mgrast_auth['token'])
        # submit job
        data = {"input_id": i['id'], "metagenome_id": rjob['metagenome_id']}
        sjob = obj_from_url(API_URL+"/job/submit", data=json.dumps(data), auth=mgrast_auth['token'])
        mgids.append(rjob['metagenome_id'])
        print "metagenome %s created for file %s (%s). submission id is: %s"%(rjob['metagenome_id'], i['filename'], i['id'], sjob['id'])
    # apply metadata
    if mdata and metadata:
        data = {"node_id": metadata, "metagenome": mgids}
        result = obj_from_url(API_URL+"/metadata/import", data=json.dumps(data), auth=mgrast_auth['token'])
        project = result['project']
        if result['errors']:
            print "ERROR: adding metadata: "+result['errors']
        else:
            print "metadata added for metagenomes"
    print "metagenomes added to project: "+project


def main(args):
    global mgrast_auth, API_URL, SHOCK_URL
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("-u", "--mgrast_url", dest="mgrast_url", default=API_URL, help="MG-RAST API url")
    parser.add_option("-s", "--shock_url", dest="shock_url", default=SHOCK_URL, help="Shock API url")
    parser.add_option("-t", "--token", dest="token", default=None, help="MG-RAST token")
    parser.add_option("-p", "--project", dest="project", default=None, help="project ID")
    parser.add_option("-m", "--metadata", dest="metadata", default=None, help="metadata file ID")
    parser.add_option("-j", "--joinfile", dest="joinfile", default=None, help="name of resulting pair-merge file (without extension), default is <pair 1 filename>_<pair 2 filename>")
    parser.add_option("", "--gzip", dest="gzip", action="store_true", default=False, help="upload file is gzip compressed")
    parser.add_option("", "--bzip2", dest="bzip2", action="store_true", default=False, help="upload file is bzip2 compressed")
    parser.add_option("", "--retain", dest="retain", action="store_true", default=False, help="retain non-overlapping sequences in pair-merge")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if len(args) < 1:
        sys.stderr.write("ERROR: missing action\n")
        return 1
    action = args[0]
    API_URL = opts.mgrast_url
    SHOCK_URL = opts.shock_url
    
    # validate inputs
    if action not in valid_actions:
        sys.stderr.write("ERROR: invalid action. use one of: %s\n"%", ".join(valid_actions))
        return 1
    elif (action == "login") and (len(args) < 2):
        sys.stderr.write("ERROR: missing login name\n")
        return 1
    elif (action == "view") and ((len(args) < 2) or (args[1] not in view_options)):
        sys.stderr.write("ERROR: invalid view option. use one of: %s\n"%", ".join(view_options))
        return 1
    elif (action in ["upload", "delete", "submit"]) and (len(args) < 2):
        sys.stderr.write("ERROR: %s missing file\n"%action)
        return 1
    elif action == "upload":
        for f in args[1:]:
            if not os.path.isfile(f):
                sys.stderr.write("ERROR: upload file '%s' does not exist\n"%f)
                return 1
    elif (action == "rename") and (len(args) != 3):
        sys.stderr.write("ERROR: %s missing file or name\n"%action)
        return 1
    elif action == "validate":
        if (len(args) < 2) or (args[1] not in validate_options):
            sys.stderr.write("ERROR: invalid validate option. use one of: %s\n"%", ".join(validate_options))
            return 1
        if len(args) < 3:
            sys.stderr.write("ERROR: validate missing file\n")
            return 1
    elif action == "compute":
        if (len(args) < 2) or (args[1] not in compute_options):
            sys.stderr.write("ERROR: invalid compute option. use one of: %s\n"%", ".join(compute_options))
            return 1
        if ( ((args[1] == "sff2fastq") and (len(args) != 3)) or
             ((args[1] in ["demultiplex", "pairjoin"]) and (len(args) != 4)) or
             ((args[1] == "pairjoin_demultiplex") and (len(args) != 5)) ):
            sys.stderr.write("ERROR: compute %s missing file(s)\n"%args[1])
            return 1
    elif (action == "submit") and (not opts.project) and (not opts.metadata):
        sys.stderr.write("ERROR: invalid submit, must have one of project or metadata\n")
        return 1
    
    # login first
    if action == "login":
        password = getpass.getpass('Enter your password: ')
        login(args[1], password)
        return 0
    
    # load auth - token overrides login
    token = get_auth_token(opts)
    mgrast_auth = get_auth(token)
    if not mgrast_auth:
        return 1
    
    # actions
    if action == "view":
        view(args[1])
    elif action == "upload":
        if opts.gzip:
            upload('gzip', args[1:])
        elif opts.bzip2:
            upload('bzip2', args[1:])
        else:
            upload('upload', args[1:])
    elif action == "rename":
        rename(args[1], args[2])
    elif action == "validate":
        validate(args[1], args[2:])
    elif action == "compute":
        compute(args[1], args[2:], opts.retain, opts.joinfile)
    elif action == "delete":
        delete(args[1:])
    elif action == "submit":
        submit(args[1:], opts.project, opts.metadata)
    
    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )

    