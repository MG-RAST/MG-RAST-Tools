#!/usr/bin/env python

import os
import sys
import json
import time
import base64
from operator import itemgetter
from optparse import OptionParser
from prettytable import PrettyTable
from mglib import *

prehelp = """
NAME
    mg-submit

VERSION
    %s

SYNOPSIS
    mg-submit
        --help
        login <user> <password>
        list
        status <submission id>
        delete <submission id>
        submit simple <seq file> [<seq file>, <seq file>, ...]
        submit batch <seq files in archive>
        submit demultiplex <seq file> <barcode file>
        submit pairjoin <pair1 seq file> <pair2 seq file> [--retain, --mg_name <name>]
        submit pairjoin_demultiplex <pair1 seq file> <pair2 seq file> <index file> [--retain, --bc_num <int>]
    
    Note:
        each 'submit' action must include one of: --project_id, --project_name, --metadata

DESCRIPTION
    MG-RAST submission client
    
    supported file types  |     extensions
    ----------------------|--------------------------
        sequence          |  .fasta, .fastq
        excel             |  .xls, .xlsx
        plain text        |  .txt, .barcode
        gzip compressed   |  .gz
        bzip2 compressed  |  .bz2
        zip archive       |  .zip
        tar archive       |  .tar, .tar.gz, .tar.bz2
    
    pipeline options      |    description
    ----------------------|---------------------------
       --assembled        |  sequences are assembeled
       --no_filter_ln     |  skip filtering fasta by sequence length
       --filter_ln_mult   |  fasta sequence length filtering multiplier
       --no_filter_ambig  |  skip filtering fasta by ambigious bps
       --max_ambig        |  maximum ambiguous bps to allow through per fasta sequence
       --no_dynamic_trim  |  skip dynamic trim of fastq sequences
       --max_lqb          |  maximum number of low-quality bases per read for fastq trimming
       --min_qual         |  quality threshold for low-quality bases for fastq trimming
       --no_dereplicate   |  skip removing technical replicates in sequence file
       --no_bowtie        |  skip filtering sequences by host organism
       --screen_indexes   |  host organism to filter sequences by
       --priority         |  indicate when making data public, influences analysis run time
"""

posthelp = """
Output
    - List submissions
    - View a submission
    - Status of command

EXAMPLES
    mg-submit list

SEE ALSO
    -

AUTHORS
    %s
"""

API_URL = "http://dev.metagenomics.anl.gov/api.cgi"
synch_pause = 900
auth_file   = os.path.join(os.path.expanduser('~'), ".mgrast_auth")
mgrast_auth = {}
valid_actions  = ["login", "list", "status", "delete", "submit"]
submit_types   = ["simple", "batch", "demultiplex", "pairjoin", "pairjoin_demultiplex"]
pipeline_flags = ["assembled", "filter_ln", "filter_ambig", "dynamic_trim", "dereplicate", "bowtie"]
pipeline_opts  = ["max_ambig", "max_lqb", "min_qual", "filter_ln_mult", "screen_indexes", "priority"]

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

def listall():
    data = obj_from_url(API_URL+"/submission/list", auth=mgrast_auth['token'])
    submissions = sorted(data['submissions'], key=itemgetter('timestamp'))
    pt = PrettyTable(["ID", "type", "status", "time"])
    for s in submissions:
        row = [ s['id'], s['type'], s['status'], s['timestamp'] ]
        pt.add_row(row)
    pt.align = "l"
    print pt

def status(sid):
    data = obj_from_url(API_URL+"/submission/"+sid, auth=mgrast_auth['token'])
    # check for errors
    if isinstance(data['status'], basestring):
        sys.stderr.write("ERROR: %s\n"%data['status'])
        sys.exit(1)
    
    fids = map(lambda x: x['id'], data['status']['inputs'])
    fnames = map(lambda x: x['filename'], data['status']['inputs'])
    # submission summary
    pt_summary = PrettyTable(["submission ID", "type", "submit time", "input file ID", "input file name"])
    pt_summary.add_row([data['id'], data['status']['type'], data['status']['timestamp'], "\n".join(fids), "\n".join(fnames)])
    pt_summary.align = "l"
    # submission status
    pt_status = PrettyTable(["submission step", "step name", "step status", "step inputs"])
    for i, p in enumerate(data['status']['preprocessing']):
        pt_status.add_row( [i, p['stage'], p['status'], "\n".join(p['inputs'])] )
    pt_status.align = "l"
    # metagenome info
    pt_mg = PrettyTable(["metagenome ID", "metagenome name", "total status", "completed steps", "total steps", "submit time", "job ID"])
    for p in data['status']['metagenomes']:
        pt_mg.add_row( [p['id'], p['name'], p['status'], p['completed'], p['total'], p['timestamp'], p['job']] )
    pt_mg.align = "l"
    # output it
    print pt_summary
    print pt_status
    if len(data['status']['metagenomes']) > 0:
        print pt_mg

def wait_on_complete(sid, json_out):
    listed_mgs = set()
    incomplete = True
    data = None
    total_mg = 0
    while incomplete:
        time.sleep(synch_pause)
        data = obj_from_url(API_URL+"/submission/"+sid, auth=mgrast_auth['token'])
        # check for global errors
        if isinstance(data['status'], basestring):
            sys.stderr.write("ERROR: %s\n"%data['status'])
            sys.exit(1)
        # check for submission errors
        for task in data['status']['preprocessing']:
            if task['status'] == "suspend":
                sys.stderr.write("ERROR: %s\n"%task['error'])
                sys.exit(1)
        # check for metagenomes
        total_mg = len(data['status']['metagenomes'])
        done_mg  = 0
        error_mg = 0
        if total_mg > 0:
            for mg in data['status']['metagenomes']:
                if mg['id'] not in listed_mgs:
                    print "metagenome analysis started: "+mg['id']
                    listed_mgs.add(mg['id'])
                if mg['status'] == "completed":
                    done_mg += 1
                elif mg['status'] == "suspend":
                    error_mg += 1
            if total_mg == (done_mg + error_mg):
                incomplete = False
    # display completed
    if json_out:
        mgs = []
        jhdl = open(json_out, 'w')
        for mg in data['status']['metagenomes']:
            if mg['status'] == "completed":
                print "metagenome analysis completed: "+mg['id']
                mgdata = obj_from_url(API_URL+"/metagenome/"+mg['id']+"?verbosity=full", auth=mgrast_auth['token'])
                mgs.append(mgdata)
            elif mg['status'] == "suspend":
                print "metagenome analysis failed: "+mg['id']
                if "error" in mg:
                    print "[error] "+mg['error']
        if len(mgs) == 1:
            # output single dict
            json.dump(mgs[0], jhdl)
        elif len(mgs) > 1:
            # output list of dicts
            json.dump(mgs, jhdl)
        else:
            # error here
            sys.stderr.write("ERROR: no metagenome(s) produced in submission %s\n"%sid)
            sys.exit(1)
        jhdl.close()
    else:
        pt_mg = PrettyTable(["metagenome ID", "metagenome name", "total status", "submit time"])
        for mg in data['status']['metagenomes']:
            pt_mg.add_row( [mg['id'], mg['name'], mg['status'], mg['timestamp']] )
        pt_mg.align = "l"
        print pt_mg

def delete(sid):
    data = obj_from_url(API_URL+"/submission/"+sid, auth=mgrast_auth['token'], method='DELETE')
    print data['status']

def seqs_from_json(json_in, tmp_dir):
    files = []
    shock_auth = "OAuth "+mgrast_auth['token']
    try:
        seq_obj = json.load(open(json_in, 'r'))
    except:
        sys.stderr.write("ERROR: %s is invalid json\n"%json_in)
        sys.exit(1)
    # simple type
    if 'handle' in seq_obj:
        stype = "simple"
        down_url  = "%s/node/%s?download"%(seq_obj['handle']['url'], seq_obj['handle']['id'])
        down_file = os.path.join(tmp_dir, seq_obj['handle']['file_name'])
        down_hdl  = open(down_file, 'w')
        file_from_url(down_url, down_hdl, sauth=shock_auth)
        down_hdl.close()
        files.append(down_file)
    # pairjoin type
    elif ('handle_1' in seq_obj) and ('handle_2' in seq_obj):
        stype = "pairjoin"
        down_url_1  = "%s/node/%s?download"%(seq_obj['handle_1']['url'], seq_obj['handle_1']['id'])
        down_url_2  = "%s/node/%s?download"%(seq_obj['handle_2']['url'], seq_obj['handle_2']['id'])
        down_file_1 = os.path.join(tmp_dir, seq_obj['handle_1']['file_name'])
        down_file_2 = os.path.join(tmp_dir, seq_obj['handle_2']['file_name'])
        down_hdl_1  = open(down_file_1, 'w')
        down_hdl_2  = open(down_file_2, 'w')
        file_from_url(down_url_1, down_hdl_1, sauth=shock_auth)
        file_from_url(down_url_2, down_hdl_2, sauth=shock_auth)
        down_hdl_1.close()
        down_hdl_2.close()
        files.append(down_file_1)
        files.append(down_file_2)
    else:
        sys.stderr.write("ERROR: input object %s is incorrect format\n"%json_in)
        sys.exit(1)
    return stype, files

def submit(stype, files, opts):
    # so far simple only
    if stype == 'batch':
        print "'batch' type submission is currently not supported."
        return
    # get files in shock
    fids = upload(files)
    # set POST data
    data = {}
    if opts.metadata:
        mid = upload([opts.metadata])
        data['metadata_file'] = mid
    elif opts.project_id:
        data['project_id'] = opts.project_id
    elif opts.project_name:
        data['project_name'] = opts.project_name
    # figure out type
    if stype == 'simple':
        data['seq_files'] = fids
    elif stype == 'demultiplex':
        data['multiplex_file'] = fids[0]
        data['barcode_file'] = fids[1]
    elif stype == 'pairjoin':
        data['pair_file_1'] = fids[0]
        data['pair_file_2'] = fids[1]
        data['retain'] = 1 if opts.retain else 0
        if opts.mgname:
            data['mg_name'] = opts.mgname
    elif stype == 'pairjoin_demultiplex':
        data['pair_file_1'] = fids[0]
        data['pair_file_2'] = fids[1]
        data['index_file'] = fids[2]
        data['retain'] = 1 if opts.retain else 0
        data['barcode_count'] = opts.bcnum
    # submit it
    result = obj_from_url(API_URL+"/submission/submit", data=json.dumps(data), auth=mgrast_auth['token'])
    if opts.synch or opts.json_out:
        print "submission started: "+result['id']
        wait_on_complete(result['id'], opts.json_out)
    else:
        status(result['id'])

def upload(files):
    fids = []
    for f in files:
        attr = json.dumps({
            "type": "inbox",
            "id": mgrast_auth['id'],
            "user": mgrast_auth['login'],
            "email": mgrast_auth['email']
        })
        # POST to shock
        fformat = "upload"
        if f.endswith(".gz"):
            fformat = "gzip"
        elif f.endswith(".bz2"):
            fformat = "bzip2"
        result = post_node(SHOCK_URL+"/node", fformat, f, attr, auth="mgrast "+mgrast_auth['token'])
        # compute file info
        info = obj_from_url(API_URL+"/inbox/info/"+result['id'], auth=mgrast_auth['token'])
        print info['status']
        fids.append(result['id'])
    return fids


def main(args):
    global mgrast_auth, API_URL, SHOCK_URL
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    # access options
    parser.add_option("-u", "--mgrast_url", dest="mgrast_url", default=API_URL, help="MG-RAST API url")
    parser.add_option("-s", "--shock_url", dest="shock_url", default=SHOCK_URL, help="Shock API url")
    parser.add_option("-t", "--token", dest="token", default=None, help="MG-RAST token")
    # required options
    parser.add_option("-m", "--metadata", dest="metadata", default=None, help="metadata file ID")
    parser.add_option("", "--project_id", dest="project_id", default=None, help="project ID")
    parser.add_option("", "--project_name", dest="project_name", default=None, help="project name")
    # pairjoin / demultiplex options
    parser.add_option("", "--mg_name", dest="mgname", default=None, help="name of pair-merge metagenome if not in metadata, default is UUID")
    parser.add_option("", "--retain", dest="retain", action="store_true", default=False, help="retain non-overlapping sequences in pair-merge")
    parser.add_option("", "--bc_num", dest="bcnum", type="int", default=0, help="number of unique barcodes in index file")
    # pipeline flags
    parser.add_option("", "--assembled", dest="assembled", action="store_true", default=False, help="if true sequences are assembeled, default is false")
    parser.add_option("", "--no_filter_ln", dest="no_filter_ln", action="store_true", default=False, help="if true skip sequence length filtering, default is on")
    parser.add_option("", "--no_filter_ambig", dest="no_filter_ambig", action="store_true", default=False, help="if true skip sequence ambiguous bp filtering, default is on")
    parser.add_option("", "--no_dynamic_trim", dest="no_dynamic_trim", action="store_true", default=False, help="if true skip qual score dynamic trimmer, default is on")
    parser.add_option("", "--no_dereplicate", dest="no_dereplicate", action="store_true", default=False, help="if true skip dereplication, default is on")
    parser.add_option("", "--no_bowtie", dest="no_bowtie", action="store_true", default=False, help="if true skip bowtie screening, default is on")
    # pipeline options
    parser.add_option("", "--filter_ln_mult", dest="filter_ln_mult", type="int", default=5, help="maximum ambiguous bps to allow through per sequence, default is 5")
    parser.add_option("", "--max_ambig", dest="max_ambig", type="int", default=5, help="maximum number of low-quality bases per read, default is 5")
    parser.add_option("", "--max_lqb", dest="max_lqb", type="int", default=15, help="quality threshold for low-quality bases, default is 15")
    parser.add_option("", "--min_qual", dest="min_qual", type="float", default=2.0, help="sequence length filtering multiplier, default is 2.0")
    parser.add_option("", "--screen_indexes", dest="screen_indexes", default=None, help="host organism to filter sequences by")
    parser.add_option("", "--priority", dest="priority", default=None, help="indicate when making data public, influences analysis run time")
    # extra modes
    parser.add_option("", "--synch", dest="synch", action="store_true", default=False, help="Run submit action in synchronious mode")
    parser.add_option("", "--json_out", dest="json_out", default=None, help="Output final metagenome product as json object to this file, synch mode only")
    parser.add_option("", "--json_in", dest="json_in", default=None, help="Input sequence file(s) encoded as shock handle in json file, simple or pairjoin types only")
    parser.add_option("", "--tmp_dir", dest="tmp_dir", default="", help="Temp dir to download too if using json_in option, default is current working dir")
    
    # get inputs
    (opts, args) = parser.parse_args()
    
    # special case
    json_submit = True if opts.json_in and os.path.isfile(opts.json_in) else False
    if json_submit:
        action = "submit"
    else:
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
    elif (action == "login") and (len(args) < 3):
        sys.stderr.write("ERROR: missing login name and password\n")
        return 1
    elif (action in ["status", "delete"]) and (len(args) < 2):
        sys.stderr.write("ERROR: %s missing submission ID\n"%action)
        return 1
    elif (action == "submit") and (not json_submit):
        if not (opts.project_id or opts.project_name or opts.metadata):
            sys.stderr.write("ERROR: invalid submit, must have one of project_id, project_name, or metadata\n")
            return 1
        if (len(args) < 2) or (args[1] not in submit_types):
            sys.stderr.write("ERROR: invalid submit option. use one of: %s\n"%", ".join(submit_types))
            return 1
        if (args[1] == "pairjoin_demultiplex") and (opts.bcnum < 2):
            sys.stderr.write("ERROR: pairjoin_demultiplex requires a minimum of 2 barcodes\n")
            return 1
        if ( ((args[1] == "simple") and (len(args) < 3)) or
             ((args[1] == "batch") and (len(args) != 3)) or
             ((args[1] in ["demultiplex", "pairjoin"]) and (len(args) != 4)) or
             ((args[1] == "pairjoin_demultiplex") and (len(args) != 5)) ):
            sys.stderr.write("ERROR: submit %s missing file(s)\n"%args[1])
            return 1
    
    # login first
    if action == "login":
        login(args[1], args[2])
        return 0
    
    # load auth - token overrides login
    token = get_auth_token(opts)
    mgrast_auth = get_auth(token)
    if not mgrast_auth:
        return 1
    
    # actions
    if action == "list":
        listall()
    elif action == "status":
        status(args[1])
    elif action == "delete":
        delete(args[1])
    elif action == "submit":
        # process input json if exists
        if json_submit:
            stype, infiles = seqs_from_json(opts.json_in, opts.tmp_dir)
        else:
            stype, infiles = args[1], args[2:]
        # get name from output json if used
        if opts.json_out and (stype == "pairjoin") and (not opts.mgname):
            opts.mgname = os.path.splitext(opts.json_out)[0]
        # submit it
        submit(stype, infiles, opts)

    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )

