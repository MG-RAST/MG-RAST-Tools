#!/usr/bin/env python
'''This script retrieves the table of sequence id, sequence, and annotation from the MG-RAST API and
dumps what it gets'''

import urllib2, json, sys, os

API_URL = "http://api.metagenomics.anl.gov/1"
# Assign the value of key from the OS environment
try:
    MGRKEY = os.environ["MGRKEY"]
except KeyError:
    MGRKEY = ""

# assign parameters
metagenome = "mgm4447943.3"
annotation_type = "feature"
source = "GenBank"
e_value = "15"
assert annotation_type in ["organism", "function", "ontology", "feature", "md5"]
assert source in ["RefSeq", "GenBank", "IMG", "SEED", "TrEMBL", "SwissProt",
    "PATRIC", "KEGG", "RDP", "Greengenes", "LSU", "SSU", "Subsystems", "NOG", "COG", "KO"]

# construct API call
# http://api.metagenomics.anl.gov/1/annotation/sequence/mgm4447943.3?type=feature&source=GenBank
base_url = API_URL + "/annotation/sequence/%s" % metagenome
base_url = base_url + "?type=%s&source=%s&auth=%s&evalue=%s" % (annotation_type, source, MGRKEY, e_value)

# retrieve the data by sending at HTTP GET request to the MG-RAST API
sys.stderr.write("Retrieving %s\n" % base_url)
try:
    opener = urllib2.urlopen(base_url)
except urllib2.HTTPError, e:
    print "Error with HTTP request: %d %s\n%s" % (e.code, e.reason, e.read())
    sys.exit(255)
opener.addheaders = [('User-agent', 'abundance_matrix.py')]

for line in opener:
    sys.stdout.write(line)
