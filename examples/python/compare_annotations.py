#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

# function to get python struct from API url
import urllib2, json
from operator import itemgetter
from prettytable import PrettyTable
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

# <codecell>

# get BIOM dump for SEED functions
seed_func = obj_from_url(api+'/matrix/function?id='+mg+'&source=SEED')

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

# for each of the top seed hits retrieve the md5s
for i, x in enumerate(seed_top):
    url = api+'/m5nr/function/'+x[0].replace(' ', '%20')+'?exact=1&source=SEED&limit=100000'
    print url
    annot = obj_from_url(url)
    md5s = dict([(a['md5'], 1) for a in annot['data']])
    seed_top[i].append(md5s.keys())

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


