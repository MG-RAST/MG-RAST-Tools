#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

# function to get python struct from API url
import urllib2, json, sys
from operator import itemgetter
from prettytable import PrettyTable
from mglib.mglib import async_rest_api, sparse_to_dense
def obj_from_url(url, data=None):
    req = urllib2.Request(url, data)
    res = urllib2.urlopen(req)
    obj = json.loads(res.read())
    return obj

# <codecell>

# variables
mg = 'mgm4447943.3'
api = 'http://api.metagenomics.anl.gov/1'
hypo = ['hypothetical', 'hyphothetical', 'putative']
if len(sys.argv) > 1:
    mg = sys.argv[1]

# <codecell>

# get BIOM dump for SEED functions
seed_func = async_rest_api(api+'/matrix/function?id='+mg+'&source=SEED')

# <codecell>

# get BIOM dump for SEED md5s
#   THIS DOES NOT SEEM TO WORK
SEED_URI = api+'/matrix/feature?id='+mg+'&source=SEED'
print(SEED_URI)
seed_md5 = async_rest_api(SEED_URI)
# <codecell>
print(seed_md5)
# set of seed md5
md5_set = set( [ x['id'] for x in seed_md5['rows'] ] )

# <codecell>

# top 5 seed functions (not hypothetical)
num = 0
seed_top = []
for s in sorted(seed_func['data'], key=itemgetter(2), reverse=True):
    skip = False
    name = seed_func['rows'][s[0]]['id']
    for h in hypo:
        if h in name:
            skip = True
    if not skip and num < 5:
        seed_top.append([name, s[2]])
        num += 1

# <codecell>

# print table: SEED annotation, abundance
x = PrettyTable(["SEED annotation", "abundance"])
x.align["SEED annotation"] = "l"
for st in seed_top:
    x.add_row([st[0], st[1]])
print x

# <codecell>

# for each of the top seed hits retrieve the md5s / only keep those in metagenome
for i, x in enumerate(seed_top):
    url = api+'/m5nr/function/'+x[0].replace(' ', '%20')+'?exact=1&source=SEED&limit=100000'
    print url
    annot = obj_from_url(url)
    md5s = set()
    for a in annot['data']:
        if "md5" in a.keys():
            md5s.add(a["md5"]) 
    seed_top[i].append(list(md5s))

# <codecell>

# print table: SEED annotation, abundance, # of md5s
x = PrettyTable(["SEED annotation", "abundance", "md5s"])
x.align["SEED annotation"] = "l"
for st in seed_top:
    x.add_row([st[0], st[1], len(st[2])])
print x

# <codecell>

# retrieve unique functions for each md5 set in GenBank space
for i, x in enumerate(seed_top):
    print x[0]
    if len(x[2]) == 0:
        seed_top[i].append([])
        continue
    data = {'source': 'GenBank', 'data': x[2], 'limit': 100000}
    annot = obj_from_url(api+'/m5nr/md5', json.dumps(data, separators=(',',':')))
    if 'ERROR' in annot:
        print annot['ERROR']
        continue
    funcs = dict([(a['function'], 1) for a in annot['data']])
    seed_top[i].append(funcs.keys())

# <codecell>

# print table: SEED annotation, abundance, # of md5s, # of GenBank annotations
x = PrettyTable(["SEED annotation", "abundance", "md5s", "GenBank annotations"])
x.align["SEED annotation"] = "l"
for st in seed_top:
    x.add_row([st[0], st[1], len(st[2]), len(st[3])])
print x

# <codecell>


