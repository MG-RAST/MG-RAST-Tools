#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

# function to get python struct from API url
import json
from operator import itemgetter
from prettytable import PrettyTable
from mglib.mglib import obj_from_url, async_rest_api

# <codecell>

# function to transform sparse matrix to dense
def sparse_to_dense(sMatrix, rmax, cmax):
    dMatrix = [[0 for i in range(cmax)] for j in range(rmax)]
    for sd in sMatrix:
        r, c, v = sd
        dMatrix[r][c] = v
    return dMatrix

# <codecell>

# variables
mgs = ['mgm4443749.3','mgm4443746.3','mgm4443747.3','mgm4443750.3','mgm4443762.3']
api = 'http://api.metagenomics.anl.gov/1'

# <codecell>

# get BIOM dump for RefSeq organisms, class taxa
refseq_class = async_rest_api(api+'/matrix/organism?id='+'&id='.join(mgs)+'&source=RefSeq&group_level=class&asynchronous=1')

# <codecell>

# build POST data for pcoa compute
rows = map(lambda x: x['id'], refseq_class['data']['rows'])
cols = map(lambda x: x['id'], refseq_class['data']['columns'])
matrix = sparse_to_dense(refseq_class['data'], len(rows), len(cols))
post_data = {"distance": "bray-curtis", "columns": cols, "rows": rows, "data": matrix}

# <codecell>

# get PCO data products via API
pcoa = async_rest_api(api+'/compute/pcoa', json.dumps(post_data, separators=(',',':')))

# <codecell>

# imports for plotting via matplotlib
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
# choose PCO to use
xpco = 1
ypco = 2
zpco = 3
# get 3D points
mgs = map(lambda d: d['id'], pcoa['data'])
xs = map(lambda d: d['pco'][xpco-1], pcoa['data'])
ys = map(lambda d: d['pco'][ypco-1], pcoa['data'])
zs = map(lambda d: d['pco'][zpco-1], pcoa['data'])
c = ['b', 'c', 'y', 'm', 'r']

# <codecell>

# plot it !
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(xs, ys, zs, c=c)
# axis labels
ax.set_xlabel('PCO %d'%xpco)
ax.set_ylabel('PCO %d'%ypco)
ax.set_zlabel('PCO %d'%zpco)
# legend
dots = []
for i, m in enumerate(mgs):
    dots.append( plt.Line2D(range(1), range(1), color='white', marker='o', markerfacecolor=c[i]) )
plt.legend(dots, mgs, numpoints=1, loc='center left', fancybox=True, shadow=True, bbox_to_anchor=(1, 0.5))
plt.show()

# <codecell>


