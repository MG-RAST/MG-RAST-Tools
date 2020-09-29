from __future__ import print_function
import os
import sys
import time
import copy
import base64
import json
import string
import time
import random
import hashlib
import subprocess
import requests
from requests_toolbelt import MultipartEncoder

try:  # python3
    from urllib.parse import urlparse, urlencode, parse_qs, quote
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:  # python2
    from urlparse import urlparse, parse_qs, quote
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError

from .__init__ import API_URL

if not sys.version_info[0:2][0] == 3 and not sys.version_info[0:2] == (2, 7) :
    sys.stderr.write('ERROR: MG-RAST Tools requires at least Python 2.7.')
    exit(1)

# don't buffer stdout
#sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

auth_file = os.path.join(os.path.expanduser('~'), ".mgrast_auth")

# return response body from MG-RAST or Shock API
def body_from_url(url, accept, auth=None, data=None, debug=False, method=None):
    header = {'Accept': accept}
    scriptname = os.path.basename(sys.argv[0])
    header['User-Agent'] = 'mglib:' + scriptname
    if auth:
        header['Authorization'] = 'mgrast '+auth
    if data or method:
        header['Content-Type'] = 'application/json'
    if debug:
        if data:
            print("data:\t"+repr(data))
        print("header:\t"+json.dumps(header))
        print("url:\t"+url)
    try:
        print("Making request "+url, file=sys.stderr)
        req = Request(url, data, headers=header)
        if method:
            req.get_method = lambda: method
        res = urlopen(req)
    except HTTPError as error:
        if debug:
            sys.stderr.write("URL: %s\n" %url)
        try:
            eobj = json.loads(error.read().decode("utf8"))
            if 'ERROR' in eobj:
                sys.stderr.write("ERROR (%s): %s\n" %(error.code, eobj['ERROR']))
            elif 'error' in eobj:
                sys.stderr.write("ERROR (%s): %s\n" %(error.code, eobj['error'][0]))
        except:
            sys.stderr.write("ERROR (%s): %s\n" %(error.code, error.read().decode("utf8")))
        finally:
            raise HTTPError(error.url, error.code, "HTTP error", error.hdrs, error.fp)
    if not res:
        sys.stderr.write("ERROR: no results returned\n")
        sys.exit(1)
    return res

# return python struct from JSON output of MG-RAST or Shock API
def obj_from_url(url, auth=None, data=None, debug=False, method=None):
    url = quote(url, safe='/:=?&', encoding="utf-8", errors="strict")
    if type(data) is str:
        data=data.encode("utf8")
    try:
        result = body_from_url(url, 'application/json', auth=auth, data=data, debug=debug, method=method)
        read = result.read()
    except:  # try one more time  ConnectionResetError is incompatible with python2
        result = body_from_url(url, 'application/json', auth=auth, data=data, debug=debug, method=method)
        read = result.read()
    if result.headers["content-type"] == "application/x-download" or result.headers["content-type"] == "application/octet-stream":
        return(read)   # Watch out!
    if result.headers["content-type"][0:9] == "text/html":  # json decoder won't work
        return(read)   # Watch out!
    if result.headers["content-type"] == "application/json":  # If header is set, this should work 
        data = read.decode("utf8")
        obj = json.loads(data)
    else:
        data = read.decode("utf8")
        obj = json.loads(data)
    if obj is None:
        sys.stderr.write("ERROR: return structure not valid json format\n" + repr(data))
        sys.exit(1)
    if len(list(obj.keys())) == 0:
        if debug:
            sys.stderr.write("URL: %s\n" %url)
        sys.stderr.write("ERROR: no data available\n")
        sys.exit(1)
    if 'ERROR' in obj:
        sys.stderr.write("ERROR: %s\n" %obj['ERROR'])
        sys.exit(1)
    if ('error' in obj) and obj['error']:
        if isinstance(obj['error'], str):
            sys.stderr.write("ERROR:\n%s\n" %obj['error'])
        else:
            sys.stderr.write("ERROR: %s\n" %obj['error'][0])
        sys.exit(1)
    return obj

# print to file results of MG-RAST or Shock API
def file_from_url(url, handle, auth=None, data=None, debug=False, sha1=False):
    result = body_from_url(url, 'text/plain', auth=auth, data=data, debug=debug)
    sha1hash = hashlib.sha1()
    while True:
        chunk = result.read(8192)
        if not chunk:
            break
        if sha1:
            sha1hash.update(chunk)
        handle.write(chunk.decode('utf8'))
    return sha1hash.hexdigest()

# print to stdout results of MG-RAST API
def stdout_from_url(url, auth=None, data=None, debug=False):
    file_from_url(url, sys.stdout, auth=auth, data=data, debug=debug)

# return python struct from JSON output of asynchronous MG-RAST API
def async_rest_api(url, auth=None, data=None, debug=False, delay=60):
    try:
        parameters = parse_qs(url.split("?")[1])
        assert "asynchronous" in parameters, "Must specify asynchronous=1 for asynchronous call!"
    except:
        parameters = {"asynchronous": 1}
    submit = obj_from_url(url, auth=auth, data=data, debug=debug)
# If "status" is nor present, or if "status" is somehow not "submitted"
# assume this is not an asynchronous call and it's done.
    if type(submit) == bytes:   # can't decode
        try: 
            return decode("utf-8", submit)
        except:
            return submit
    if ('status' in submit) and (submit['status'] != 'submitted') and (submit['status'] != "processing") and ('data' in submit):
        return submit
    if not ('url' in submit.keys()):
        return submit
#    if not (('status' in submit) and (submit['status'] == 'submitted') and ('url' in submit)):
#        return submit  # No status, no url and no submitted
    result = obj_from_url(submit['url'], auth=auth, debug=debug)
    if type(result) is bytes:
        return(result)
    if 'status' in result.keys():
        while result['status'] == 'submitted' or result['status'] == "processing":
            if debug:
                print("waiting %d seconds ..."%delay)
            time.sleep(delay)
            result = obj_from_url(submit['url'], auth=auth, debug=debug)
    if 'url' in result.keys() or 'next' in result.keys(): # does not need to wait
        return(result)
    try:
        print("Error in response to "+url, file=sys.stderr)
        print("Does not contain 'status' or 'next' field, likely API syntax error", file=sys.stderr)
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)
    except TypeError:  # result isn't json, return it anyway
        return(result.decode("utf8"))
    try:
        if 'ERROR' in result['data']:
            sys.stderr.write("ERROR: %s\n" %result['data']['ERROR'])
            print(json.dumps(result), file=sys.stderr)
            sys.exit(1)
    except KeyError:  # result doesn't have "data"
        return result
    return result['data']

# POST file to MG-RAST or Shock
def post_file(url, keyname, filename, data={}, auth=None, debug=False):

    if debug:
        print("post_file", url)
    data[keyname] = (os.path.basename(filename), open(filename, 'rb'))
    datagen = MultipartEncoder(data)
    header = {"Content-Type": datagen.content_type}
    if auth:
        header['Authorization'] = 'mgrast '+auth
    if debug:
        print("data:\t"+repr(data))
        print("header:\t"+repr(header))
        print("url:\t"+url)

    success = False
    sleep   = 60
    maxt    = 3
    counter = 0
    obj     = None

    # try maxt times
    while not success and counter < maxt :
        try:
            res = requests.post(url, data=datagen, headers=header, stream=True)
        except HTTPError as error:
            try:
                eobj = json.loads(error.read())
                if 'ERROR' in eobj:
                    sys.stderr.write("ERROR (%s): %s\n" %(error.code, eobj['ERROR']))
                elif 'error' in eobj:
                    sys.stderr.write("ERROR (%s): %s\n" %(error.code, eobj['error'][0]))
            except:
                sys.stderr.write("ERROR (%s): %s\n" %(error.code, error.read()))
            finally:
                # sys.exit(1)
                return None
        except OSError as error: 
            sys.stderr.write("ERROR with post_file\n")
            sys.stderr.write("ERROR (%s): %s\n" %(error.code, error.read()))
        if not res:
            sys.stderr.write("ERROR: no results returned for %s\n"% (filename))
            # sys.exit(1)
        else: 
            obj = json.loads(res.content.decode("utf8"))
            if debug:
                print(json.dumps(obj))
            if obj is None:
                sys.stderr.write("ERROR: return structure not valid json format\n")
            else:
                success = True
        # increase counter
        if not success :
            counter += 1
            time.sleep(counter * sleep)
    return(obj)

# safe handling of stdout for piping
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
# returns max value of matrix
def biom_to_tab(biom, hdl, rows=None, use_id=True, col_name=False):
    assert 'matrix_type' in biom.keys(), repr(biom)
    if biom['matrix_type'] == 'sparse':
        matrix = sparse_to_dense(biom['data'], biom['shape'][0], biom['shape'][1])
    else:
        matrix = biom['data']
    if col_name:
        hdl.write("\t%s\n" %"\t".join([c['name'] for c in biom['columns']]))
    else:
        hdl.write("\t%s\n" %"\t".join([c['id'] for c in biom['columns']]))
    rowmax = []
    for i, row in enumerate(matrix):
        name = biom['rows'][i]['id']
        if (not use_id) and ('ontology' in biom['rows'][i]['metadata']):
            name += ':'+biom['rows'][i]['metadata']['ontology'][-1]
        if rows and (name not in rows):
            continue
        try:
            rowmax.append(max(row))
            hdl.write("%s\t%s\n" %(name, "\t".join(map(str, row))))
        except:
            try:
                hdl.close()
            except:
                pass
    return max(rowmax)

# retrieve a list of metadata values from biom file columns for given term
# order is same as columns
def metadata_from_biom(biom, term):
    vals = []
    for col in biom['columns']:
        value = 'null'
        if ('metadata' in col) and col['metadata']:
            for v in col['metadata'].values():
                if ('data' in v) and (term in v['data']):
                    value = v['data'][term]
        vals.append(value)
    return vals

# turn profile format BIOM into matrix format, use only abundances
def profile_to_matrix(p):
    if p['columns'][0]['id'] != 'abundance':
        # not a profile
        return p
    trim = True if len(p['columns']) > 1 else False
    p['columns'][0]['id'] = p['id']
    p['matrix_element_type'] = 'int'
    p['matrix_element_value'] = 'abundance'
    p['date'] = time.strftime("%Y-%m-%d %H:%M:%S")
    assert 'matrix_type' in p.keys(), repr(p)
    if p['matrix_type'] == 'sparse':
        p['data'] = sparse_to_dense(p['data'], p['shape'][0], p['shape'][1])
    if trim:
        p['columns'] = p['columns'][:1]
        for i in range(len(p['rows'])):
            p['data'][i] = p['data'][i][:1]
    return p

# merge two BIOM objects
def merge_biom(b1, b2):
    """input: 2 biom objects of same 'type', 'matrix_element_type', and 'matrix_element_value'
    return: merged biom object, duplicate columns skipped, duplicate rows added"""
    # hack for using in loop when one of 2 is empty
    if b1 and (not b2):
        return b1
    if b2 and (not b1):
        return b2
    # transform profile BIOM from UI export into matrix BIOM
    b1 = profile_to_matrix(b1)
    b2 = profile_to_matrix(b2)
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
    assert 'matrix_type' in b2.keys(), repr(b2)
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
    if "columns" not in biom.keys():
       biom = biom["data"]
    if col_name:
        cols = [c['name'] for c in biom['columns']]
    else:
        cols = [c['id'] for c in biom['columns']]
    try:
        rows = [";".join(r['metadata']['taxonomy']) for r in biom['rows']]
    except KeyError:
        rows = [r['id'] for r in biom['rows']]
#        rows = [";".join(r['metadata']['hierarchy']) for r in biom['rows']]
    assert "matrix_type" in biom.keys(), repr(biom)
    if biom['matrix_type'] == 'sparse':
        data = sparse_to_dense(biom['data'], len(rows), len(cols))
    else:
        data = biom['data']
    if sig_stats and ('significance' in biom['rows'][0]['metadata']) and (len(biom['rows'][0]['metadata']['significance']) > 0):
        cols.extend([s[0] for s in biom['rows'][0]['metadata']['significance']] )
        for i, r in enumerate(biom['rows']):
            data[i].extend([s[1] for s in r['metadata']['significance']] )
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
        sub.append(row[:ncols] )
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
    data = obj_from_url(API_URL+'/job/'+request, auth=auth, data=post)
    return data['data']

def get_auth_token(opts=None):
    if 'KB_AUTH_TOKEN' in os.environ:
        return os.environ['KB_AUTH_TOKEN']
    if 'MGRKEY' in os.environ:
        return os.environ['MGRKEY']
    if hasattr(opts, "token") and opts.token is not None:
        return opts.token
    elif hasattr(opts, 'user') and hasattr(opts, 'passwd') and (opts.user or opts.passwd):
        if opts.user and opts.passwd:
            return token_from_login(opts.user, opts.passwd)
        else:
            sys.stderr.write("ERROR: both username and password are required\n")
            sys.exit(1)
    else:
        return ""

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

def token_from_login(user, passwd):
    auth = 'kbgo4711'+base64.b64encode('%s:%s' %(user, passwd)).replace('\n', '')
    data = obj_from_url(API_URL, auth=auth)
    return data['token']

def login(token):
    auth_obj = obj_from_url(API_URL+"/user/authenticate", auth=token)
    json.dump(auth_obj, open(auth_file,'w'))

def login_from_token(token):
    parts = {}
    for part in token.strip().split('|'):
        key, val = part.split('=')
        parts[key] = val
    return parts['un']

def random_str(size=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for x in range(size))

# this is a bit of a hack, need to redo using rpy2
def execute_r(cmd, debug=False):
    r_cmd = "echo '%s' | R --vanilla --slave --silent"%cmd
    if debug:
        print(r_cmd)
    else:
        process = subprocess.Popen(r_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        if error:
            sys.stderr.write(error)
            sys.exit(1)

def _cmd_exists(cmd):
    return subprocess.call("type %s"%cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
