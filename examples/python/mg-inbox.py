#!/usr/bin/env python

import os
import sys
import json
import time
import urllib2
import cStringIO
from operator import itemgetter
from optparse import OptionParser

try:
    from prettytable import PrettyTable
except ImportError:
    sys.stderr.write("[error] prettytable library is missing, use 'pip install prettytable'\n")
    sys.exit(1)

try:
    import requests
except ImportError:
    sys.stderr.write("[error] requests library is missing, use 'pip install requests'\n")
    sys.exit(1)

try:
    from requests_toolbelt import MultipartEncoder
except ImportError:
    sys.stderr.write("[error] requests_toolbelt library is missing, use 'pip install prettytable'\n")
    sys.exit(1)


prehelp = """
NAME
    mg-inbox

VERSION
    1

SYNOPSIS
    mg-inbox
        --help
        login [--token <auth token>]
        view all
        view sequence
        upload <file> <file> ...
        upload-archive <archive file>
        rename <file id> <new name>
        validate sequence <seq file id> <seq file id> ...
        validate metadata <excel file id> <excel file id> ...
        compute sff2fastq <sff file id>
        compute demultiplex <seq file id> <barcode file id> [<index file id>, --rc_index]
        compute pairjoin <pair1 seq file id> <pair2 seq file id> [--retain, --joinfile <filename>]
        compute pairjoin_demultiplex <pair1 seq file id> <pair2 seq file id> <index file id> <barcode file id> [--retain, --rc_index]
        delete <file id> <file id> ...
        submit <file id> <file id> ... [--project <project id>, --metadata <file id>]

DESCRIPTION
    MG-RAST inbox operations
    
    supported file types  |     extensions
    ----------------------|--------------------------
        sequence          |  .fasta, .fastq
        excel             |  .xls, .xlsx
        plain text        |  .txt, .barcode
        gzip compressed   |  .gz
        bzip2 compressed  |  .bz2
        zip archive       |  .zip
        tar archive       |  .tar, .tar.gz, .tar.bz2
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
    Jared Bischof, Travis Harrison, Folker Meyer, Tobias Paczian, Andreas Wilke
"""

API_URL = "http://api.metagenomics.anl.gov"
SHOCK_URL = "http://shock.metagenomics.anl.gov"

auth_file   = os.path.join(os.path.expanduser('~'), ".mgrast_auth")
mgrast_auth = {}
valid_actions    = ["login", "view", "upload", "upload-archive", "rename", "validate", "compute", "delete", "submit", "submitall"]
view_options     = ["all", "sequence"]
validate_options = ["sequence", "metadata"]
compute_options  = ["sff2fastq", "demultiplex", "pairjoin", "pairjoin_demultiplex"]

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

# POST file to Shock
def post_node(url, keyname, filename, attr, auth=None):
    data = {
        keyname: (os.path.basename(filename), open(filename)),
        'attributes': ('unknown', cStringIO.StringIO(attr))
    }
    mdata = MultipartEncoder(fields=data)
    headers = {'Content-Type': mdata.content_type}
    if auth:
        headers['Authorization'] = auth
    try:
        req = requests.post(url, headers=headers, data=mdata, allow_redirects=True)
        rj = req.json()
    except:
        sys.stderr.write("Unable to connect to Shock server")
        sys.exit(1)
    if rj and rj['error']:
        sys.stderr.write("Shock error %s: %s"%(rj['status'], rj['error'][0]))
        sys.exit(1)
    if not (req.ok):
        sys.stderr.write("Unable to connect to Shock server")
        sys.exit(1)
    return rj['data']

# unpack archive node into new nodes
def unpack_node(url, parent_id, aformat, attr, auth=None):
    data = {
        'unpack_node': parent_id,
        'archive_format': aformat,
        'attributes_str': attr
    }
    mdata = MultipartEncoder(fields=data)
    headers = {'Content-Type': mdata.content_type}
    if auth:
        headers['Authorization'] = auth
    try:
        req = requests.post(url, headers=headers, data=mdata, allow_redirects=True)
        rj = req.json()
    except:
        sys.stderr.write("Unable to connect to Shock server")
        sys.exit(1)
    if rj and rj['error']:
        sys.stderr.write("Shock error %s: %s"%(rj['status'], rj['error'][0]))
        sys.exit(1)
    if not (req.ok):
        sys.stderr.write("Unable to connect to Shock server")
        sys.exit(1)
    return rj['data']

def get_auth(token):
    if token:
        auth_obj = obj_from_url(API_URL+"/user/authenticate", auth=token)
        return auth_obj
    if not os.path.isfile(auth_file):
        sys.stderr.write("ERROR: missing authentication file, please login\n")
        return None
    auth_obj = json.load(open(auth_file,'r'))
    if ("token" not in auth_obj) or ("id" not in auth_obj) or ("expiration" not in auth_obj):
        sys.stderr.write("ERROR: invalid authentication file, please login\n")
        return None
    if time.time() > int(auth_obj["expiration"]):
        sys.stderr.write("ERROR: expired authentication file, please login\n")
        return None
    return auth_obj

def login(token):
    auth_obj = obj_from_url(API_URL+"/user/authenticate", auth=token)
    json.dump(auth_obj, open(auth_file,'w'))

def check_ids(files):
    data = obj_from_url(API_URL+"/inbox", auth=mgrast_auth['token'])
    if len(data['files']) == 0:
        sys.stderr.write("ERROR: Your inbox is empty, please upload first.\n")
        sys.exit(1)
    ids = map(lambda x: x['id'], data['files'])
    for f in files:
        if f not in ids:
            sys.stderr.write("ERROR: File ID '%s' does not exist in your inbox. Did you use File Name by mistake?\n"%f)
            sys.exit(1)

def view(vtype):
    data = obj_from_url(API_URL+"/inbox", auth=mgrast_auth['token'])
    files = sorted(data['files'], key=itemgetter('timestamp'))
    action_set = filter(lambda x: ("actions" in x) and (len(x['actions']) > 0), files)
    has_action = True if len(action_set) > 0 else False
    has_error = False
    if has_action:
        for f in action_set:
            for a in f['actions']:
                a['name'] = a['name'].replace("stats", "validation")
                if ('error' in a) and a['error']:
                    has_error = True
    header = ["ID", "name", "md5sum", "size", "time", "format"]
    
    if vtype == "sequence":
        header = header + ["seq_type", "seq_count", "bp_count"]
        if has_action:
            header.append("actions")
            if has_error:
                header.append("error")
        pt = PrettyTable(header)
        for f in files:
            if ('data_type' in f) and (f['data_type'] == 'sequence'):
                row = [
                    f['id'],
                    f['filename'],
                    f['checksum'],
                    f['filesize'],
                    f['timestamp'].split(".")[0],
                    f['stats_info']['file_type'],
                    f['stats_info']['sequence_type'],
                    f['stats_info']['sequence_count'],
                    f['stats_info']['bp_count']
                ]
                if has_action:
                    row.append([])
                    for a in f['actions']:
                        row[9].append(a['name']+": "+a['status'])
                    row[9] = "\n".join(row[9])
                    if has_error:
                        row.append([])
                        for a in f['actions']:
                            if ('error' in a) and a['error']:
                                row[10].append(a['name']+": "+a['error'])
                        row[10] = "\n".join(row[10])
                pt.add_row(row)
    else:
        if has_action:
            header.append("actions")
            if has_error:
                header.append("error")
        pt = PrettyTable(header)
        for f in files:
            row = [
                f['id'],
                f['filename'],
                f['checksum'],
                f['filesize'],
                f['timestamp'].split(".")[0],
                f['stats_info']['file_type']
            ]
            if has_action:
                row.append([])
                for a in f['actions']:
                    row[6].append(a['name']+": "+a['status'])
                row[6] = "\n".join(row[6])
                if has_error:
                    row.append([])
                    for a in f['actions']:
                        if ('error' in a) and a['error']:
                            row[7].append(a['name']+": "+a['error'])
                    row[7] = "\n".join(row[7])
            pt.add_row(row)
    pt.align = "r"
    pt.align['name'] = "l"
    pt.align['time'] = "l"
    print pt

def upload(files):
    for f in files:
        attr = json.dumps({
            "type": "inbox",
            "id": mgrast_auth['id'],
            "user": mgrast_auth['login'],
            "email": mgrast_auth['email']
        })
        # get format
        if f.endswith(".gz"):
            fformat = "gzip"
        elif f.endswith(".bz2"):
            fformat = "bzip2"
        else:
            fformat = "upload"
        # POST to shock
        result = post_node(SHOCK_URL+"/node", fformat, f, attr, auth="mgrast "+mgrast_auth['token'])
        # compute file info
        info = obj_from_url(API_URL+"/inbox/info/"+result['id'], auth=mgrast_auth['token'])
        print info['status']
        # compute sequence stats
        if info['stats_info']['file_type'] in ['fasta', 'fastq']:
            stats = obj_from_url(API_URL+"/inbox/stats/"+result['id'], auth=mgrast_auth['token'])
            print stats['status'].replace("stats computation", "validation")

def upload_archive(afile):
    attr = json.dumps({
        "type": "inbox",
        "id": mgrast_auth['id'],
        "user": mgrast_auth['login'],
        "email": mgrast_auth['email']
    })
    # get format
    if afile.endswith(".tar.gz"):
        aformat = "tar.gz"
    elif afile.endswith(".tar.bz2"):
        aformat = "tar.bz2"
    elif afile.endswith(".tar"):
        aformat = "tar"
    elif afile.endswith(".zip"):
        aformat = "zip"
    else:
        sys.stderr.write("ERROR: input file %s is incorrect archive format\n"%afile)
        sys.exit(1)
    # POST to shock / unpack
    result = post_node(SHOCK_URL+"/node", "upload", afile, attr, auth="mgrast "+mgrast_auth['token'])
    unpack = unpack_node(SHOCK_URL+"/node", result['id'], aformat, attr, auth="mgrast "+mgrast_auth['token'])
    # process new nodes
    for node in unpack:
        # compute file info
        info = obj_from_url(API_URL+"/inbox/info/"+node['id'], auth=mgrast_auth['token'])
        print info['status']
        # compute sequence stats
        if info['stats_info']['file_type'] in ['fasta', 'fastq']:
            stats = obj_from_url(API_URL+"/inbox/stats/"+node['id'], auth=mgrast_auth['token'])
            print stats['status'].replace("stats computation", "validation")

def rename(fid, fname):
    data = {"name": fname, "file": fid}
    result = obj_from_url(API_URL+"/inbox/rename", data=json.dumps(data), auth=mgrast_auth['token'])
    print result['status']

def validate(fformat, files, get_info=False):
    for f in files:
        data = obj_from_url(API_URL+"/inbox/"+f, auth=mgrast_auth['token'])
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

def compute(action, files, retain, joinfile, rc_index):
    if action == "sff2fastq":
        data = {"sff_file": files[0]}
    elif action == "demultiplex":
        data = {
            "seq_file": files[0],
            "barcode_file": files[1],
            "rc_index": 1 if rc_index else 0
        }
        if len(files) == 3:
            data["index_file"] = files[2]
    elif action == "pairjoin":
        data = {
            "pair_file_1": files[0],
            "pair_file_2": files[1],
            "retain": 1 if retain else 0
        }
        if joinfile:
            data['output'] = joinfile
    elif action == "pairjoin_demultiplex":
        data = {
            "pair_file_1": files[0],
            "pair_file_2": files[1],
            "index_file": files[2],
            "barcode_file": files[3],
            "retain": 1 if retain else 0,
            "rc_index": 1 if rc_index else 0
        }
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
        print "metagenome %s created for file %s (%s). pipeline id is: %s"%(rjob['metagenome_id'], i['filename'], i['id'], sjob['awe_id'])
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
    parser = OptionParser(usage='', description=prehelp, epilog=posthelp)
    parser.add_option("-u", "--mgrast_url", dest="mgrast_url", default=API_URL, help="MG-RAST API url")
    parser.add_option("-s", "--shock_url", dest="shock_url", default=SHOCK_URL, help="Shock API url")
    parser.add_option("-t", "--token", dest="token", default=None, help="MG-RAST token")
    parser.add_option("-p", "--project", dest="project", default=None, help="project ID")
    parser.add_option("-m", "--metadata", dest="metadata", default=None, help="metadata file ID")
    parser.add_option("-j", "--joinfile", dest="joinfile", default=None, help="name of resulting pair-merge file (without extension), default is <pair 1 filename>_<pair 2 filename>")
    parser.add_option("", "--retain", dest="retain", action="store_true", default=False, help="retain non-overlapping sequences in pair-merge")
    parser.add_option("", "--rc_index", dest="rc_index", action="store_true", default=False, help="barcodes in index file are reverse compliment of mapping file")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if len(args) < 1:
        sys.stderr.write("ERROR: missing action, please check usage with %s -h\n"%(sys.argv[0]))
        return 1
    action = args[0]
    API_URL = opts.mgrast_url
    SHOCK_URL = opts.shock_url
    
    # validate inputs
    if action not in valid_actions:
        sys.stderr.write("ERROR: invalid action. use one of: %s\n"%", ".join(valid_actions))
        return 1
    elif (action == "view") and ((len(args) < 2) or (args[1] not in view_options)):
        sys.stderr.write("ERROR: invalid view option. use one of: %s\n"%", ".join(view_options))
        return 1
    elif (action in ["upload", "upload-archive", "delete", "submit"]) and (len(args) < 2):
        sys.stderr.write("ERROR: %s missing file\n"%action)
        return 1
    elif action == "upload":
        for f in args[1:]:
            if not os.path.isfile(f):
                sys.stderr.write("ERROR: upload file '%s' does not exist\n"%f)
                return 1
    elif action == "upload-archive":
        if len(args[1:]) > 1:
            sys.stderr.write("ERROR: upload-archive only supports one file\n")
            return 1
        if not os.path.isfile(args[1]):
            sys.stderr.write("ERROR: upload-archive file '%s' does not exist\n"%args[1])
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
             ((args[1] == "demultiplex") and (len(args) < 4)) or
             ((args[1] == "pairjoin") and (len(args) != 4)) or
             ((args[1] == "pairjoin_demultiplex") and (len(args) != 6)) ):
            sys.stderr.write("ERROR: compute %s missing file(s)\n"%args[1])
            return 1
    elif (action == "submit") and (not opts.project) and (not opts.metadata):
        sys.stderr.write("ERROR: invalid submit, must have one of project or metadata\n")
        return 1
    
    # explict login
    if action == "login":
        if not opts.token:
            opts.token = raw_input('Enter your MG-RAST auth token: ')
        login(opts.token)
        return 0
    
    # get auth object, get from token if no login
    mgrast_auth = get_auth(opts.token)
    if not mgrast_auth:
        return 1
    
    # actions
    if action == "view":
        view(args[1])
    elif action == "upload":
        upload(args[1:])
    elif action == "upload-archive":
        upload_archive(args[1])
    elif action == "rename":
        check_ids([args[1]])
        rename(args[1], args[2])
    elif action == "validate":
        check_ids(args[2:])
        validate(args[1], args[2:])
    elif action == "compute":
        check_ids(args[2:])
        compute(args[1], args[2:], opts.retain, opts.joinfile, opts.rc_index)
    elif action == "delete":
        check_ids(args[1:])
        delete(args[1:])
    elif action == "submit":
        check_ids(args[1:])
        submit(args[1:], opts.project, opts.metadata)
    
    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )

    