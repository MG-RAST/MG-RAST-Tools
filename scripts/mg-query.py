#!/usr/bin/env python
'''This script retrieves a URI from the MG-RAST API, handling authorization
and asyncrhonous requests for the user.'''

from __future__ import print_function
import sys
from argparse import ArgumentParser
import json
from mglib import async_rest_api, get_auth_token

DEBUG = 0

if __name__ == '__main__':
    usage = "usage: %prog [options]  URI"
    parser = ArgumentParser(usage)
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")
    parser.add_argument("-k", "--token", dest="token", type=str,
                      help="Auth token")
    parser.add_argument("URI", type=str, help="URI to query")

    opts = parser.parse_args()
    key = get_auth_token(opts)
    if opts.verbose:
        print("KEY = {}".format(key), file=sys.stderr)   
# assign parameters
    URI = opts.URI

# construct API call
    print(URI, file=sys.stderr)

# retrieve the data by sending at HTTP GET request to the MG-RAST API
    jsonstructure = async_rest_api(URI, auth=key)

# unpack and display the data table
    if type(jsonstructure) == dict:    # If we have data, not json structure
        print(json.dumps(jsonstructure), file=sys.stdout)
    else:
        try:
            sys.stdout.write(jsonstructure.decode("utf-8"))
        except UnicodeDecodeError:
            sys.stdout.buffer.write(jsonstructure)
