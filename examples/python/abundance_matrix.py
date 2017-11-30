#!/usr/bin/env python
'''This script retrieves a metagenome_statistics data structure from the MG-RAST API and
plots a graph using data from the web interface'''

import urllib2, json, sys, os
from mglib.mglib import async_rest_api, sparse_to_dense
DEBUG=0
API_URL = "http://api.metagenomics.anl.gov/1"
# Assign the value of key from the OS environment
try:
    key = os.environ["MGRKEY"]
except KeyError:
    key = ""

# assign parameters
metagenomes = ["mgm4447943.3", "mgm4447102.3"]
group_level = "domain"
result_type = "abundance"
source = "SEED"

# construct API call 
base_url = API_URL + "/matrix/organism"
base_url = base_url + "?asynchronous=1&group_level=%s&result_type=%s&auth=%s&source=%s&evalue=15&" % (group_level, result_type, key, source) 
URI = base_url + "&".join( [ "id=%s" % m for m in metagenomes ] ) 

# retrieve the data by sending at HTTP GET request to the MG-RAST API

jsonstructure = async_rest_api(URI, auth=key)

# unpack and display the data table
cols = [x["id"] for x in jsonstructure["columns"]]
rows = [x["id"] for x in jsonstructure["rows"] ] 
matrixtype = jsonstructure["type"]

if matrixtype == "sparse":
    data = sparse_to_dense(jsonstructure["data"], len(rows), len(cols))
else: 
    data = jsonstructure["data"]

if DEBUG:
    print(jsonstructure)
    print("COLS", cols)
    print("ROWS", rows)
    print("TYPE", matrixtype)
    print("DATA", data)
h=data
 
sys.stdout.write("Taxon\t") 
for j in range(0, len(cols) ):
    sys.stdout.write(cols[j] +"\t")
print
for i in range( 0, len(rows)):
    sys.stdout.write(rows[i]+"\t") 
    for j in range( 0, len(cols)):
        try:
            sys.stdout.write(str(h[i][j])+"\t" )
        except KeyError:
            sys.stdout.write("0\t")
    sys.stdout.write("\n")

