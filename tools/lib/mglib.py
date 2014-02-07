import os
import sys
import time
import copy
import urllib2
import base64
import json
import string
import random
import subprocess

# don't buffer stdout
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

VERSION = '1'
API_URL = "http://api.metagenomics.anl.gov/"+VERSION
AUTH_LIST = "Jared Bischof, Travis Harrison, Folker Meyer, Tobias Paczian, Andreas Wilke"
SEARCH_FIELDS = ["function", "organism", "md5", "name", "biome", "feature", "material", "country", "location", "longitude", "latitude", "created", "env_package_type", "project_id", "project_name", "PI_firstname", "PI_lastname", "sequence_type", "seq_method", "collection_date"]

# return python struct from JSON output of asynchronous MG-RAST API
def async_rest_api(url, auth=None, data=None, debug=False, delay=15):
    submit = obj_from_url(url, auth=auth, data=data, debug=debug)
    if not (('status' in submit) and (submit['status'] == 'Submitted') and ('url' in submit)):
        sys.stderr.write("ERROR: return data invalid format\n:%s"%json.dumps(submit))
    result = obj_from_url(submit['url'], debug=debug)
    while result['status'] != 'done':
        if debug:
            print "waiting %d seconds ..."%delay
        time.sleep(delay)
        result = obj_from_url(submit['url'], debug=debug)
    if 'ERROR' in result['data']:
        sys.stderr.write("ERROR: %s\n" %result['data']['ERROR'])
        sys.exit(1)
    return result['data']

# return python struct from JSON output of MG-RAST API
def obj_from_url(url, auth=None, data=None, debug=False):
    header = {'Accept': 'application/json'}
    if auth:
        header['Auth'] = auth
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
            sys.stderr.write("ERROR (%s): %s\n" %(error.code, eobj['ERROR']))
            sys.exit(1)
        except:
            sys.stderr.write("ERROR (%s): %s\n" %(error.code, error.read()))
            sys.exit(1)
    if not res:
        sys.stderr.write("ERROR: no results returned\n")
        sys.exit(1)
    obj = json.loads(res.read())
    if obj is None:
        sys.stderr.write("ERROR: return structure not valid json format\n")
        sys.exit(1)
    if len(obj.keys()) == 0:
        sys.stderr.write("ERROR: no data available\n")
        sys.exit(1)
    if 'ERROR' in obj:
        sys.stderr.write("ERROR: %s\n" %obj['ERROR'])
        sys.exit(1)
    return obj

# print to stdout results of MG-RAST API
def stdout_from_url(url, auth=None, data=None, debug=False):
    header = {'Accept': 'text/plain'}
    if auth:
        header['Auth'] = auth
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
            sys.stderr.write("ERROR (%s): %s\n" %(error.code, eobj['ERROR']))
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
        safe_print(chunk)

# safe handeling of stdout for pipeing
def safe_print(text):
    text = "".join([x if ord(x) < 128 else '?' for x in text])
    try:
        sys.stdout.write(text)
    except IOError:
        # stdout is closed, no point in continuing
        # Attempt to close them explicitly to prevent cleanup problems:
        try:
            sys.stdout.close()
        except IOError:
            pass
        try:
            sys.stderr.close()
        except IOError:
            pass

# transform sparse matrix to dense matrix (2D array)
def sparse_to_dense(sMatrix, rmax, cmax):
    dMatrix = [[0 for i in range(cmax)] for j in range(rmax)]
    for sd in sMatrix:
        r, c, v = sd
        dMatrix[r][c] = v
    return dMatrix

# transform BIOM format to tabbed table
def biom_to_tab(biom, hdl, rows=None, use_id=True, col_name=False):
    if biom['matrix_type'] == 'sparse':
        matrix = sparse_to_dense(biom['data'], biom['shape'][0], biom['shape'][1])
    else:
        matrix = biom['data']
    if col_name:
        hdl.write( "\t%s\n" %"\t".join([c['name'] for c in biom['columns']]) )
    else:
        hdl.write( "\t%s\n" %"\t".join([c['id'] for c in biom['columns']]) )
    for i, row in enumerate(matrix):
        name = biom['rows'][i]['id']
        if (not use_id) and ('ontology' in biom['rows'][i]['metadata']):
            name += ':'+biom['rows'][i]['metadata']['ontology'][-1]
        if rows and (name not in rows):
            continue
        try:
            hdl.write( "%s\t%s\n" %(name, "\t".join([str(r) for r in row])) )
        except:
            try:
                hdl.close()
            except:
                pass

# retrieve a list of metadata values from biom file columns for given term
# order is same as columns
def metadata_from_biom(biom, term):
    vals = []
    for col in biom['columns']:
        value = 'null'
        if ('metadata' in col) and col['metadata']:
            for v in col['metadata'].itervalues():
                if ('data' in v) and (term in v['data']):
                    value = v['data'][term]
        vals.append(value)
    return vals

# merge two BIOM objects
def merge_biom(b1, b2):
    """input: 2 biom objects of same 'type', 'matrix_element_type', and 'matrix_element_value'
    return: merged biom object, duplicate columns skipped, duplicate rows added"""
    # hack for using in loop when one oif 2 is empty
    if b1 and (not b2):
        return b1
    if b2 and (not b1):
        return b2
    # validate
    if not (b1 and b2 and (b1['type'] == b2['type']) and (b1['matrix_element_type'] == b2['matrix_element_type']) and (b1['matrix_element_value'] == b2['matrix_element_value'])):
        sys.stderr.write("The inputed biom objects are not compatable for merging\n")
        return None
    # build
    mBiom = { "generated_by": b1['generated_by'],
               "matrix_type": 'dense',
               "date": time.strftime("%Y-%m-%d %H:%M:%S"),
               "columns": copy.deepcopy(b1['columns']),
               "rows": copy.deepcopy(b1['rows']),
               "data": sparse_to_dense(b1['data'], b1['shape'][0], b1['shape'][1]) if b1['matrix_type'] == 'sparse' else copy.deepcopy(b1['data']),
               "shape": [],
               "matrix_element_value": b1['matrix_element_value'],
               "matrix_element_type": b1['matrix_element_type'],
               "format_url": "http://biom-format.org",
               "format": "Biological Observation Matrix 1.0",
               "id": b1['id']+'_'+b2['id'],
               "type": b1['type'] }
    # make sure we are dense
    if b2['matrix_type'] == 'sparse':
        b2['data'] = sparse_to_dense(b2['data'], b2['shape'][0], b2['shape'][1])
    # get lists of ids
    c1_id = [c['id'] for c in b1['columns']]
    r1_id = [r['id'] for r in b1['rows']]
    r2_id = [r['id'] for r in b2['rows']]
    c2_keep = 0
    # merge columns, skip duplicate by id
    for c in b2['columns']:
        if c['id'] not in c1_id:
            mBiom['columns'].append(c)
            c2_keep += 1
    # merge b2-cols into b1-rows
    for i, r in enumerate(mBiom['rows']):
        add_row = []
        try:
            # b1-row is in b2, use those values
            r2_index = r2_id.index(r['id'])
            for j, c in enumerate(b2['columns']):
                if c['id'] not in c1_id:
                    add_row.append(b2['data'][r2_index][j])
        except:
            # b1-row not in b2, add 0's
            add_row = [0]*c2_keep
        mBiom['data'][i].extend(add_row)
    # add b2-rows that are not in b1
    for i, r in enumerate(b2['rows']):
        if r['id'] in r1_id:
            continue
        # b1-col all 0's
        add_row = [0]*b1['shape'][1]
        # add b2-cols
        for j, c in enumerate(b2['columns']):
            if c['id'] not in c1_id:
                add_row.append(b2['data'][i][j])
        mBiom['rows'].append(r)
        mBiom['data'].append(add_row)
    mBiom['shape'] = [ len(mBiom['rows']), len(mBiom['columns']) ]
    return mBiom

# transform BIOM format to matrix in json format
def biom_to_matrix(biom, col_name=False, sig_stats=False):
    if col_name:
        cols = [c['name'] for c in biom['columns']]
    else:
        cols = [c['id'] for c in biom['columns']]
    rows = [r['id'] for r in biom['rows']]
    if biom['matrix_type'] == 'sparse':
        data = sparse_to_dense(biom['data'], len(rows), len(cols))
    else:
        data = biom['data']
    if sig_stats and ('significance' in biom['rows'][0]['metadata']) and (len(biom['rows'][0]['metadata']['significance']) > 0):
        cols.extend( [s[0] for s in biom['rows'][0]['metadata']['significance']] )
        for i, r in enumerate(biom['rows']):
            data[i].extend( [s[1] for s in r['metadata']['significance']] )
    return rows, cols, data

# transform tabbed table to matrix in json format
def tab_to_matrix(indata):
    lines = indata.split('\n')
    data = []
    rows = []
    cols = lines[0].strip().split('\t')
    for line in lines[1:]:
        parts = line.strip().split('\t')
        first = parts.pop(0)
        if len(cols) == len(parts):
            rows.append(first)
            data.append(parts)
    return rows, cols, data

# return a subselection of matrix columns
def sub_matrix(matrix, ncols):
    if ncols >= len(matrix[0]):
        return matrix
    sub = list()
    for row in matrix:
        sub.append( row[:ncols] )
    return sub

# return KBase id for MG-RAST id
def mgid_to_kbid(mgid):
    id_map = kbid_lookup([mgid], reverse=True)
    return id_map[mgid] if mgid in id_map else None

# return MG-RAST id for given KBase id
def kbid_to_mgid(kbid):
    id_map = kbid_lookup([kbid])
    if kbid not in id_map:
        sys.stderr.write("ERROR: '%s' not a valid KBase ID\n" %kbid)
        sys.exit(1)
    return id_map[kbid]

# return list of MG-RAST ids for given list of KBase ids
#  handels mixed ids / all mgrast ids
def kbids_to_mgids(kbids):
    id_map = kbid_lookup(kbids)
    mgids = []
    for i in kbids:
        if i in id_map:
            mgids.append(id_map[i])
        else:
            mgids.append(i)
    return mgids

# return map (KBase id -> MG-RAST id) for given list of KBase ids
#  or reverse
def kbid_lookup(ids, reverse=False):
    request = 'mg2kb' if reverse else 'kb2mg'
    post = json.dumps({'ids': ids}, separators=(',',':'))
    data = obj_from_url(API_URL+'/job/'+request, data=post)
    return data['data']

def get_auth_token(opts):
    if 'KB_AUTH_TOKEN' in os.environ:
        return os.environ['KB_AUTH_TOKEN']
    if opts.token:
        return opts.token
    elif opts.user or opts.passwd:
        if opts.user and opts.passwd:
            return token_from_login(opts.user, opts.passwd)
        else:
            sys.stderr.write("ERROR: both username and password are required\n")
            sys.exit(1)
    else:
        return None

def token_from_login(user, passwd):
    auth = 'kbgo4711'+base64.b64encode('%s:%s' %(user, passwd)).replace('\n', '')
    data = obj_from_url(API_URL, auth=auth)
    return data['token']

def load_to_ws(wname, otype, oname, obj):
    if not _cmd_exists('ws-load'):
        sys.stderr.write('ERROR: missing workspace client\n')
    tmp_ws = 'tmp_'+random_str()+'.txt'
    json.dump(obj, open(tmp_ws, 'w'))
    ws_cmd = "ws-load %s %s %s -w %s"%(otype, oname, tmp_ws, wname)
    process = subprocess.Popen(ws_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    os.remove(tmp_ws)
    if error:
        sys.stderr.write(error)
        sys.exit(1)
    else:
        sys.stdout.write("%s saved in workspace %s as type %s\n"%(oname, wname, otype))

def random_str(size=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for x in range(size))

# this is a bit of a hack, need to redo using rpy2
def execute_r(cmd, debug=False):
    r_cmd = "echo '%s' | R --vanilla --slave --silent"%cmd
    if debug:
        print r_cmd
    else:
        process = subprocess.Popen(r_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        if error:
            sys.stderr.write(error)
            sys.exit(1)

def _cmd_exists(cmd):
    return subprocess.call("type %s"%cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
