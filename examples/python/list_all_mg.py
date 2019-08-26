#!/usr/bin/env python
'''This script retrieves a list of metagenomes from the MG-RAST API.'''
from __future__ import print_function
from __future__ import unicode_literals
import sys
import time

from mglib import get_auth_token, obj_from_url, API_URL, urlencode

def printlist(js):
    '''prints essential fields from metagenome list'''
    for item in js["data"]:
        if "public" in item.keys():
            public = item["public"]
        else:
            public = "False"
        try:
            mg_name= item["name"]
            project_id = item["project_id"]
            project_name = item["project_name"]
        except KeyError:
            sys.stderr.write(repr(item))
        sys.stdout.write(("\t".join([item["metagenome_id"],
#                        str(len(item.keys())),
                         repr(public), item["created_on"],
                         mg_name, project_id, project_name]) + "\n"))

CALL = "/search"

key = get_auth_token()

# assign parameters
limit = 1000 # initial call

# construct API call
# public = 0 means "don't show public metagenomes"
parameters = {"limit": limit, "order":"created_on", "direction": "asc", "public": "1"}
API_URL= "https://api.mg-rast.org/"

base_url = API_URL + CALL + "?" + urlencode(parameters)

# convert the data from a JSON structure to a python data type, a dict of dicts.
jsonstructure = obj_from_url(base_url, auth=key)

# unpack and display the data table
total_count = int(jsonstructure["total_count"])
sys.stderr.write("Total number of records: {:d}\n".format(total_count))

for i in range(0, int(total_count / limit) +1):
    sys.stderr.write("Page {:d}\t".format(i))
    jsonstructure = obj_from_url(base_url, auth=key)
    printlist(jsonstructure)
    time.sleep(3)
    try:
        next_url = jsonstructure["next"]
        base_url = next_url
    except KeyError:
        break
