#!/usr/bin/env python
'''This script retrieves a metagenome_statistics data structure from the MG-RAST API and
plots a graph using data from the web interface'''

import urllib2, json, sys, os

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
base_url = base_url + "?group_level=%s&result_type=%s&auth=%s&source=%s&evalue=15&" % (group_level, result_type, key, source) 
base_url = base_url + "&".join( [ "id=%s" % m for m in metagenomes ] ) 

# retrieve the data by sending at HTTP GET request to the MG-RAST API
sys.stderr.write("Retrieving %s\n" % base_url)
try:
    opener = urllib2.urlopen(base_url)
except urllib2.HTTPError, e:
    print "Error with HTTP request: %d %s\n%s" % (e.code, e.reason, e.read())
    sys.exit(255)
opener.addheaders = [('User-agent', 'abundance_matrix.py')]

jsonobject = opener.read()

# convert the data from a JSON structure to a python data type, a dict of dicts.
jsonstructure = json.loads(jsonobject)

# unpack and display the data table
cols = jsonstructure["columns"]
rows = jsonstructure["rows"]
data = jsonstructure["data"]
 
h = { (a, b) : int(c) for (a, b, c) in data } 
sys.stdout.write("Taxon\t") 
for j in range(0, len(cols) ):
    sys.stdout.write(cols[j]["id"] +"\t")
print
for i in range( 0, len(rows)):
    sys.stdout.write(str(rows[i]["id"])+"\t") 
    for j in range( 0, len(cols)):
        try:
            sys.stdout.write(str(h[(i, j)])+"\t" )
        except KeyError:
            sys.stdout.write("0\t")
    sys.stdout.write("\n")

