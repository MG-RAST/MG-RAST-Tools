import os
import sys
import time
import urllib2
import base64
import json

# don't buffer stdout
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

VERSION = '1'
API_URL = "http://api.metagenomics.anl.gov/"+VERSION
AUTH_LIST = "Jared Bischof, Travis Harrison, Folker Meyer, Tobias Paczian, Andreas Wilke"
SEARCH_FIELDS = ["function", "organism", "name", "biome", "feature", "material", "country", "location", "longitude", "latitude", "created", "env_package_type", "project_id", "project_name", "PI_firstname", "PI_lastname", "sequence_type", "seq_method", "collection_date"]

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
def biom_to_tab(biom, hdl, rows=None, use_id=True):
    matrix = sparse_to_dense(biom['data'], biom['shape'][0], biom['shape'][1])
    hdl.write( "\t%s\n" %"\t".join([c['id'] for c in biom['columns']]) )
    for i, row in enumerate(matrix):
        name = biom['rows'][i]['id'] if use_id else biom['rows'][i]['metadata']['ontology'][-1]
        if rows and (name not in rows):
            continue
        hdl.write( "%s\t%s\n" %(name, "\t".join([str(r) for r in row])) )

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
