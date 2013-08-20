#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

'''This script retrieves a metagenome_statistics data structure from the MG-RAST API and
plots a graph using data from the web interface'''

import urllib, json, sys
import numpy as np
from prettytable import PrettyTable

# MG-RAST API url
API_URL = "http://api.metagenomics.anl.gov/1"

# <codecell>

# retrieve the data by sending at HTTP GET request to the MG-RAST API
ACCESSIONNUMBER = "mgm4440613.3" # this is a public job

some_url = "%s/metagenome/%s?verbosity=stats" % (API_URL, ACCESSIONNUMBER)
sys.stderr.write("Retrieving %s\n" % some_url)
jsonobject = urllib.urlopen(some_url).read()

# <codecell>

# convert the data from a JSON structure to a python data type, a dict of dicts.
jsonstructure = json.loads(jsonobject)

# get the elements of the data that we want out of the dict of dicts..
spectrum = np.array( jsonstructure["statistics"]["qc"]["kmer"]["15_mer"]["data"], dtype="float")
lengthdistribution = np.array( jsonstructure["statistics"]["length_histogram"]["upload"], dtype="int")
lengthdistribution2 = np.array( jsonstructure["statistics"]["length_histogram"]["post_qc"], dtype="int")

# <codecell>

# print table of first 10 rows: 
x = PrettyTable(['count of kmer','count of count','col1 x col2','sum col2','sum col3','col5 / sum col3'])
for s in spectrum[0:10]:
    x.add_row(s)
print x

# <codecell>

# plot the length distribution graph
import matplotlib.pyplot as plt
plt.plot(lengthdistribution[:, 0], lengthdistribution[:, 1], label="uploaded")
plt.plot(lengthdistribution2[:, 0], lengthdistribution2[:, 1], label="post qc")
plt.xlabel("length (bp)")
plt.ylabel("number of reads")
plt.title("Length distribution for %s" % ACCESSIONNUMBER )
plt.legend()
plt.show()

# <codecell>


