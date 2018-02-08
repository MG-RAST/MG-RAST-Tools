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
from mglib.mglib import *

prehelp = """
NAME
    mg-submit

VERSION
    %s

SYNOPSIS
    mg-submit
        --help
        login [--token <auth token>]
        list
        status <submission id>
        delete <submission id>
        submit simple <seq file> [<seq file>, <seq file>, ...]
        submit batch <seq files in archive>
        submit demultiplex <seq file> <barcode file> [<index file>, --rc_index]
        submit pairjoin <pair1 seq file> <pair2 seq file> [--retain, --mg_name <name>]
        submit pairjoin_demultiplex <pair1 seq file> <pair2 seq file> <index file> <barcode file> [--retain, --rc_index]
    
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

synch_pause = 900
mgrast_auth = {}
valid_actions = ["login", "list", "status", "delete", "submit"]
submit_types  = ["simple", "batch", "demultiplex", "pairjoin", "pairjoin_demultiplex"]

def listall():
    data = obj_from_url(API_URL+"/submission/list", auth=mgrast_auth['token'])
    submissions = sorted(data['submissions'], key=itemgetter('timestamp'))
    pt = PrettyTable(["ID", "type", "status", "time"])
    for s in submissions:
        row = [ s['id'], s['type'], s['status'], s['timestamp'] ]
        pt.add_row(row)
    pt.align = "l"
    print(pt)

def status(sid):
    data = obj_from_url(API_URL+"/submission/"+sid+'?full=1', auth=mgrast_auth['token'])
    # check for errors
<<<<<<< HEAD
    if ('error' in data) and data['error']:
        sys.stderr.write("ERROR: %s\n"%data['error'])
        sys.exit(1)
    
    fids   = map(lambda x: x['id'], data['inputs'])
    fnames = map(lambda x: x['filename'], data['inputs'])
    fsizes = map(lambda x: str(x['filesize']), data['inputs'])
=======
    if isinstance(data['status'], str):
        sys.stderr.write("ERROR: %s\n"%data['status'])
        sys.exit(1)
    
    fids = [x['id'] for x in data['status']['inputs']]
    fnames = [x['filename'] for x in data['status']['inputs']]
>>>>>>> 10b155dc4a101f7859d170f536b3a0fa74185892
    # submission summary
    pt_summary = PrettyTable(["submission ID", "type", "project", "submit time", "input file ID", "input file name", "input file size", "status"])
    pt_summary.add_row([data['id'], data['type'], data['project'], data['info']['submittime'], "\n".join(fids), "\n".join(fnames), "\n".join(fsizes), data['state']])
    pt_summary.align = "l"
    print(pt_summary)
    # submission status
    if ('preprocessing' in data) and data['preprocessing']:
        pt_status = PrettyTable(["submission step", "step name", "step status", "step inputs"])
        for i, p in enumerate(data['preprocessing']):
            pstatus = p['status']
            if ('error' in p) and p['error']:
                pstatus += "\n"+p['error']
            pt_status.add_row( [i, p['stage'], pstatus, "\n".join(p['inputs'])] )
        pt_status.align = "l"
        print(pt_status)
    # metagenome info
    if ('metagenomes' in data) and data['metagenomes']:
        pt_mg = PrettyTable(["metagenome ID", "metagenome name", "status", "remaining steps", "submit time", "complete time", "pipeline ID"])
        for m in data['metagenomes']:
            state = "in-progress"
            if len(m['state']) == 1:
                state = m['state'][0]
            else:
                for s in m['state']:
                    if s == 'suspend':
                        state = 'suspend'
            remain = 0
            if m['task'] and (len(m['task']) > 0):
                remain = len(m['task'])
            pt_mg.add_row( [m['userattr']['id'], m['userattr']['name'], state, remain, m['submittime'], m['completedtime'], m['id']] )
        pt_mg.align = "l"
        print(pt_mg)

def wait_on_complete(sid, json_out):
    listed_mgs = set()
    incomplete = True
    data = None
    total_mg = 0
    while incomplete:
        time.sleep(synch_pause)
        data = obj_from_url(API_URL+"/submission/"+sid, auth=mgrast_auth['token'])
        # check for global errors
        if isinstance(data['status'], str):
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
                    print("metagenome analysis started: "+mg['id'])
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
                print("metagenome analysis completed: "+mg['id'])
                mgdata = obj_from_url(API_URL+"/metagenome/"+mg['id']+"?verbosity=full", auth=mgrast_auth['token'])
                mgs.append(mgdata)
            elif mg['status'] == "suspend":
                print("metagenome analysis failed: "+mg['id'])
                if "error" in mg:
                    print("[error] "+mg['error'])
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
        print(pt_mg)

def delete(sid):
    data = obj_from_url(API_URL+"/submission/"+sid, auth=mgrast_auth['token'], method='DELETE')
    print(data['status'])

def seqs_from_json(json_in, tmp_dir):
    files = []
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
        file_from_url(down_url, down_hdl, auth=mgrast_auth['token'])
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
        file_from_url(down_url_1, down_hdl_1, auth=mgrast_auth['token'])
        file_from_url(down_url_2, down_hdl_2, auth=mgrast_auth['token'])
        down_hdl_1.close()
        down_hdl_2.close()
        files.append(down_file_1)
        files.append(down_file_2)
    else:
        sys.stderr.write("ERROR: input object %s is incorrect format\n"%json_in)
        sys.exit(1)
    return stype, files

def submit(stype, files, opts):
    fids = []
    # post files to shock
    if stype == 'batch':
        fids = archive_upload(files[0], opts.verbose)
    else:
        fids = upload(files, opts.verbose)
    
    # set POST data
    data = {}
    if opts.debug:
        data['debug'] = 1
    if opts.metadata:
        mids = upload([opts.metadata], opts.verbose)
        data['metadata_file'] = mids[0]
    elif opts.project_id:
        data['project_id'] = opts.project_id
    elif opts.project_name:
        data['project_name'] = opts.project_name
    # figure out type
    if (stype == 'simple') or (stype == 'batch'):
        data['seq_files'] = fids
    elif stype == 'demultiplex':
        data['multiplex_file'] = fids[0]
        data['barcode_file'] = fids[1]
        data['rc_index'] = 1 if opts.rc_index else 0
        if len(fids) == 3:
            data["index_file"] = fids[2]
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
        data['barcode_file'] = fids[3]
        data['retain'] = 1 if opts.retain else 0
        data['rc_index'] = 1 if opts.rc_index else 0
    
    # set pipeline flags - assembeled is special case
    if opts.assembled:
        data['assembled'] = 1
        data['filter_ln'] = 0
        data['filter_ambig'] = 0
        data['dynamic_trim'] = 0
        data['dereplicate'] = 0
        data['bowtie'] = 0
    else:
        data['assembled'] = 0
        data['filter_ln'] = 0 if opts.no_filter_ln else 1
        data['filter_ambig'] = 0 if opts.no_filter_ambig else 1
        data['dynamic_trim'] = 0 if opts.no_dynamic_trim else 1
        data['dereplicate'] = 0 if opts.no_dereplicate else 1
        data['bowtie'] = 0 if opts.no_bowtie else 1
    # set pipeline options
    data['filter_ln_mult'] = opts.filter_ln_mult
    data['max_ambig'] = opts.max_ambig
    data['max_lqb'] = opts.max_lqb
    data['min_qual'] = opts.min_qual
    if opts.screen_indexes:
        data['screen_indexes'] = opts.screen_indexes
    if opts.priority:
        data['priority'] = opts.priority
    
    # submit it
    if opts.verbose:
        print("Submitting to MG-RAST with the following parameters:")
        print(json.dumps(data, sort_keys=True, indent=4))
    result = obj_from_url(API_URL+"/submission/submit", data=json.dumps(data), auth=mgrast_auth['token'])
    if opts.verbose and (not opts.debug):
        print(json.dumps(result))
    if opts.debug:
        pprint.pprint(result)
    elif opts.synch or opts.json_out:
        print("Project ID: "+result['project'])
        print("Submission ID: "+result['id'])
<<<<<<< HEAD
=======
        print("submission started: "+result['id'])
>>>>>>> 10b155dc4a101f7859d170f536b3a0fa74185892
        wait_on_complete(result['id'], opts.json_out)
    else:
        print("Project ID: "+result['project'])
        print("Submission ID: "+result['id'])
        status(result['id'])

def upload(files, verbose):
    fids = []
    attr = json.dumps({
        "type": "inbox",
        "id": mgrast_auth['id'],
        "user": mgrast_auth['login'],
        "email": mgrast_auth['email']
    })
    for i, f in enumerate(files):
        # get format
        if f.endswith(".gz"):
            fformat = "gzip"
            fname = os.path.basename(f[:-3])
        elif f.endswith(".bz2"):
            fformat = "bzip2"
            fname = os.path.basename(f[:-4])
        else:
            fformat = "upload"
            fname = os.path.basename(f)
        # POST to shock
        data = {
            "file_name": fname,
            "attributes_str": attr
        }
        if verbose:
            if len(files) > 1:
                print("Uploading file %d of %d (%s) to MG-RAST Shock"%(i+1, len(files), f))
            else:
                print("Uploading file %s to MG-RAST Shock"%(f))
        result = post_file(SHOCK_URL+"/node", fformat, f, data=data, auth=mgrast_auth['token'], debug=verbose)
        if verbose:
            print(json.dumps(result['data']))
            if len(files) > 1:
                print("Setting info for file %d of %d (%s) in MG-RAST inbox"%(i+1, len(files), f))
            else:
                print("Setting info for file %s in MG-RAST inbox"%(f))
        # compute file info
        info = obj_from_url(API_URL+"/inbox/info/"+result['data']['id'], auth=mgrast_auth['token'], debug=verbose)
        if verbose:
            print(json.dumps(info))
        else:
            print(info['status'])
        fids.append(result['data']['id'])
    return fids

def archive_upload(afile, verbose):
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
    if verbose:
        print("Uploading file %s to MG-RAST Shock"%(afile))
    data = {
        "file_name": os.path.basename(afile),
        "attributes_str": attr
    }
    result = post_file(SHOCK_URL+"/node", "upload", afile, data=data, auth=mgrast_auth['token'], debug=verbose)
    if verbose:
        print(json.dumps(result['data']))
        print("Unpacking archive file %s"%(afile))
    data = {
        "unpack_node": result['data']['id'],
        "archive_format": aformat,
        "attributes_str": attr
    }
    unpack = obj_from_url(SHOCK_URL+"/node", data=data, auth=mgrast_auth['token'], debug=verbose)
    if verbose:
        print(json.dumps(unpack['data']))
    fids = map(lambda x: x['id'], unpack['data'])
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
    parser.add_option("-m", "--metadata", dest="metadata", default=None, help="metadata .xlsx file")
    parser.add_option("", "--project_id", dest="project_id", default=None, help="project ID")
    parser.add_option("", "--project_name", dest="project_name", default=None, help="project name")
    # pairjoin / demultiplex options
    parser.add_option("", "--mg_name", dest="mgname", default=None, help="name of pair-merge metagenome if not in metadata, default is UUID")
    parser.add_option("", "--retain", dest="retain", action="store_true", default=False, help="retain non-overlapping sequences in pair-merge")
    parser.add_option("", "--rc_index", dest="rc_index", action="store_true", default=False, help="barcodes in index file are reverse compliment of mapping file")
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
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="Verbose STDOUT")
    parser.add_option("", "--debug", dest="debug", action="store_true", default=False, help="Submit in debug mode")
    
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
    
    if opts.verbose and opts.debug:
        print("##### Running in Debug Mode #####")
    
    # validate inputs
    if action not in valid_actions:
        sys.stderr.write("ERROR: invalid action. use one of: %s\n"%", ".join(valid_actions))
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
        if ( ((args[1] == "simple") and (len(args) < 3)) or
             ((args[1] == "batch") and (len(args) != 3)) or
             ((args[1] == "demultiplex") and (len(args) < 4)) or
             ((args[1] == "pairjoin") and (len(args) != 4)) or
             ((args[1] == "pairjoin_demultiplex") and (len(args) != 6)) ):
            sys.stderr.write("ERROR: submit %s missing file(s)\n"%args[1])
            return 1
    
    # explict login
    token = get_auth_token(opts)
    if action == "login":
        if not token:
            token = input('Enter your MG-RAST auth token: ')
        login(token)
        return 0
    
    # get auth object, get from token if no login
    mgrast_auth = get_auth(token)
    if not mgrast_auth:
        return 1
    
    # actions
    if action == "list":
        if opts.verbose:
            print("Listing all submissions for "+mgrast_auth['login'])
        listall()
    elif action == "status":
        if opts.verbose:
            print("Status for submission"+args[1])
        status(args[1])
    elif action == "delete":
        if opts.verbose:
            print("Deleting submission"+args[1])
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
        if opts.verbose:
            print("Starting submission %s for %d files"%(stype, len(infiles)))
        submit(stype, infiles, opts)

    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )

