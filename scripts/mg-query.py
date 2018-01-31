#!/usr/bin/env python
'''This script retrieves a URI from the MG-RAST API, handling authorization
and asyncrhonous requests for the user.'''

from __future__ import print_function
import sys
from optparse import OptionParser
import json
from mglib.mglib import async_rest_api, get_auth_token

DEBUG = 0
API_URL = "http://api.metagenomics.anl.gov/1"

if __name__ == '__main__':
    usage = "usage: %prog [options]  URI"
    parser = OptionParser(usage)
#    parser.add_option("-v", "--verbose", dest="verbose", action="store_true")
    parser.add_option("-k", "--token", dest="token", type="str",
                      help="Auth token")

    (opts, args) = parser.parse_args()
    key = get_auth_token(opts)

# assign parameters
    URI = args[0]

# construct API call
    print(URI, file=sys.stderr)

# retrieve the data by sending at HTTP GET request to the MG-RAST API
    jsonstructure = async_rest_api(URI, auth=key)

# unpack and display the data table
    print(json.dumps(jsonstructure))
