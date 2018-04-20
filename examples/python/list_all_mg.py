#!/usr/bin/env python2
'''This script retrieves a list of metagenomes from the MG-RAST API.'''
from __future__ import print_function
import urllib
import sys

from mglib import get_auth_token, obj_from_url, API_URL

def printlist(js):
    '''prints essential fields from metagenome list'''
    for item in js["data"]:
        if "public" in item.keys():
            public = repr(item["public"])
        else:
            public = "False"
        sys.stdout.write( ("\t".join([item["metagenome_id"],
#                         str(len(item.keys())),
                          public, item["created_on"],
                          item["name"]]) + "\n").encode("utf-8"))

CALL = "/search"

key = get_auth_token()

# assign parameters
limit = 1000 # initial call

# construct API call

parameters = {"limit": limit, "auth": key, "order":"created_on", "direction": "asc"}
base_url = API_URL + CALL + "?" + urllib.urlencode(parameters)

# convert the data from a JSON structure to a python data type, a dict of dicts.
jsonstructure = obj_from_url(base_url)

# unpack and display the data table
total_count = int(jsonstructure["total_count"])
sys.stderr.write("Total number of records: {:d}\n".format(total_count))

for i in range(0, total_count / limit +1):
    sys.stderr.write("Page {:d}\t".format(i))
    jsonstructure = obj_from_url(base_url)
    printlist(jsonstructure)
    try:
        next_url = jsonstructure["next"]
        base_url = next_url
    except KeyError:
        break
