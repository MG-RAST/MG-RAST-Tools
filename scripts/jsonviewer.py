#!/usr/bin/env python

import sys
import json
from optparse import OptionParser

prehelp = """
NAME
    jsonviewer

VERSION
    1

SYNOPSIS
    jsonviewer [ --help, --info, --json, --keys, --value <key or index>, --find <key name> ]

DESCRIPTION
    View data in JSON structure.
"""

posthelp = """
Input
    Valid JSON structure

Output
    Varies based on option used
    1. default is list of tab-deliminated key-value pairs if hash, elements if array
    2. option to ourpur JSON structure
    3. option to list hash keys or number of array elements

EXAMPLES
    echo '{"a": {"b": {"c": [1, 2, 3, 4, 5]}}, "x": ["y", "z"], "foo": "bar"}' | jsonviewer
    echo '{"a": {"b": {"c": [1, 2, 3, 4, 5]}}, "x": ["y", "z"], "foo": "bar"}' | jsonviewer --value 'a.b.c' --json

SEE ALSO
    -

AUTHORS
    Travis Harrison
"""

def jsontype(jdata):
    if isinstance(jdata, dict):
        return 'object'
    elif isinstance(jdata, list):
        return 'list'
    else:
        sys.stderr.write("ERROR: Invalid JSON structure, must be object or list\n")
        return None

def get_values(data, path, key):
    sub_iter = []
    if isinstance(data, dict):
        if key in data:
            np = path+[key]
            yield data[key], np
        sub_iter = data.iteritems()
    if isinstance(data, list):
        sub_iter = enumerate(data)
    for k, x in sub_iter:
        np = path+[k]
        for y, p in get_values(x, np, key):
            yield y, p

def get_depth(data, depth=0):
    if not data:
        return depth
    elif isinstance(data, dict):
        return max(get_depth(v, depth+1) for k, v in data.iteritems())
    elif isinstance(data, list):
        return max(get_depth(e, depth+1) for e in data)
    else:
        return depth

def to_string(x, dump=False, keys=False, expand=False, summary=False):
    if isinstance(x, dict):
        if summary:
            return "<object>"
        elif dump:
            return json.dumps(x, sort_keys=True, indent=4) if expand else json.dumps(x, sort_keys=True)
        elif keys:
            return "\n".join(sorted(x.keys()))
        else:
            return "\n".join(map(lambda k: "%s\t%s"%(str(k), to_string(x[k], summary=True)), sorted(x.keys())))
    elif isinstance(x, list):
        if summary:
            return "<list>"
        elif dump:
            return json.dumps(x, sort_keys=True, indent=4) if expand else json.dumps(x, sort_keys=True)
        elif keys:
            return len(x)
        else:
            return "\n".join(map(lambda e: to_string(e, summary=True), x))
    else:
        return str(x)

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp, epilog=posthelp)
    parser.add_option("", "--info", dest="info", action="store_true", default=False, help="give format and depth of JSON structure")
    parser.add_option("", "--json", dest="json", action="store_true", default=False, help="pretty print of JSON structure")
    parser.add_option("", "--keys", dest="keys", action="store_true", default=False, help="list of keys if hash, number of elements if array")
    parser.add_option("", "--value", dest="value", default=None, help="value for a given key name or array index, use dot (.) to indicate multiple levels")
    parser.add_option("", "--find", dest="find", default=None, help="value(s) for a given key name at any depth")

    # get inputs
    (opts, args) = parser.parse_args()
    try:
        jdata = json.load(sys.stdin)
    except:
        sys.stderr.write("ERROR: No JSON object could be decoded\n")
        return 1
    jtype = jsontype(jdata)
    if not jtype:
        return 1
    vlist = []
    if opts.value:
        vlist = opts.value.split('.')
    
    # ouput
    if opts.info:
        depth = get_depth(jdata)
        print "type\t%s\ndepth\t%d"%(jtype, depth)
    if (not opts.value) and (opts.json or opts.keys):
        print to_string(jdata, dump=opts.json, keys=opts.keys, expand=True)
    elif opts.value and (len(vlist) > 0):
        data = jdata
        path = []
        for k in vlist:
            path.append(k)
            try:
                if isinstance(data, dict) and (k in data):
                    data = data[k]
                elif isinstance(data, list) and (int(k) < len(data)):
                    data = data[int(k)]
                else:
                    sys.stderr.write("ERROR: (%s) is not a key/index path of inputted JSON\n"%', '.join(path))
                    return 1
            except:
                sys.stderr.write("ERROR: (%s) is not a key/index path of inputted JSON\n"%', '.join(path))
                return 1
        print to_string(data, dump=opts.json, keys=opts.keys, expand=True)
    elif opts.find:
        for val, path in get_values(jdata, [], opts.find):
            print ".".join(path)+"\t"+to_string(val, dump=True)
    # default list top level
    else:
        print to_string(jdata)
    return 0

if __name__ == "__main__":
    sys.exit( main(sys.argv) )