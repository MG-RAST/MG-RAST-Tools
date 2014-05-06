#!/usr/bin/env python

import sys
import urllib
from collections import defaultdict
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-get-annotation-set

VERSION
    %s

SYNOPSIS
    mg-get-annotation-set [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --id <metagenome id>, --level <taxon level>, --top <top N abundant organsims>, --rest, --source <datasource>, --evalue <evalue negative exponent>, --identity <percent identity>, --length <alignment length> ]

DESCRIPTION
    Retrieve functional annotations for given metagenome and organism.
"""

posthelp = """
Output
    Tab-delimited list of annotations: feature list, function, abundance for function, avg evalue for function, organism

EXAMPLES
    mg-get-annotation-set --id "kb|mg.287" --top 5 --level genus --source SEED

SEE ALSO
    -

AUTHORS
    %s
"""

# output annotations
def output_annotation(md5s, func_md5, func_acc, amatrix, ematrix, otu):
    for f in sorted(func_md5.iterkeys()):
        abund = 0
        evalue = 0.0
        for i, m in enumerate(md5s):
            if m in func_md5[f]:
                abund += amatrix[i][0]
                evalue += ematrix[i][0]
        # output: feature list, function, abundance for function, avg evalue for function, organism
        safe_print("%s\t%s\t%d\t%.2e\t%s\n" %(",".join(func_acc[f]), f, abund, 10**(evalue/len(func_md5[f])), otu))

# get annotations for taxa
def annotations_for_taxa(opts, md5s, taxa, inverse=False):
    func_md5 = defaultdict(set)
    func_acc = defaultdict(set)
    tax_post = { 'data': taxa,
                 'source': opts.source,
                 'tax_level': opts.level,
                 'limit': 1000,
                 'version': '1',
                 'exact': '1' }
    if inverse:
        tax_post['inverse'] = '1'

    # group annotations by function containing features
    # process by chunks of md5s
    size = 5000
    for i in xrange(0, len(md5s), size):
        sub_md5s = md5s[i:i+size]
        tax_post['md5s'] = sub_md5s
        tax_post['data'] = taxa
        tax_post['offset'] = 0
        # get data from m5nr
        while True:
            # get paginated data
            ann_data = obj_from_url(opts.url+'/m5nr/organism', data=json.dumps(tax_post, separators=(',',':')))
            for a in ann_data['data']:
                # skip md5s not in this set
                if a['md5'] not in sub_md5s:
                    continue
                func_md5[a['function']].add(a['md5'])
                func_acc[a['function']].add(a['accession'])
            # determine next paginated query
            if (ann_data['limit'] + ann_data['offset']) >= ann_data['total_count']:
                break
            tax_post['offset'] = ann_data['limit'] + ann_data['offset']
    
    # return function data
    return func_md5, func_acc

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--id", dest="id", default=None, help="KBase Metagenome ID, required")
    parser.add_option("", "--url", dest="url", default=API_URL, help="communities API url")
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")
    parser.add_option("", "--level", dest="level", default='species', help="taxon level to group annotations by, default is species")
    parser.add_option("", "--top", type="int", dest="top", default=10, help="produce annotations for top N abundant organisms, default is 10")
    parser.add_option("", "--rest", dest="rest", action="store_true", default=False, help="lump together remaining organisms after top N, default is off")
    parser.add_option("", "--source", dest="source", default='SEED', help="datasource to filter results by, default is SEED")
    parser.add_option("", "--evalue", type="int", dest="evalue", default=5, help="negative exponent value for maximum e-value cutoff, default is 5")
    parser.add_option("", "--identity", type="int", dest="identity", default=60, help="percent value for minimum % identity cutoff, default is 60")
    parser.add_option("", "--length", type="int", dest="length", default=15, help="value for minimum alignment length cutoff, default is 15")
    
    # get inputs
    (opts, args) = parser.parse_args()
    opts.top = int(opts.top)
    if not opts.id:
        sys.stderr.write("ERROR: id required\n")
        return 1
    
    # get auth
    token = get_auth_token(opts)
    if opts.id.startswith('kb|'):
        opts.id = kbid_to_mgid(opts.id)
    
    # get top taxa
    top_taxa = []
    t_params = [ ('id', opts.id),
                 ('group_level', opts.level),
                 ('source', opts.source),
                 ('evalue', opts.evalue),
                 ('identity', opts.identity),
                 ('length', opts.length),
                 ('result_type', 'abundance'),
                 ('asynchronous', '1'),
                 ('hide_metadata', '1') ]
    t_url = opts.url+'/matrix/organism?'+urllib.urlencode(t_params, True)
    biom = async_rest_api(t_url, auth=token)
    for d in sorted(biom['data'], key=itemgetter(2), reverse=True):
        if (opts.top > 0) and (len(top_taxa) >= opts.top):
            break
        top_taxa.append( biom['rows'][d[0]]['id'] )
    
    # get feature data
    f_params = [ ('id', opts.id),
                 ('source', opts.source),
                 ('evalue', opts.evalue),
                 ('identity', opts.identity),
                 ('length', opts.length),
                 ('asynchronous', '1'),
                 ('hide_metadata', '1'),
                 ('hide_annotation', '1') ]
    f_url = opts.url+'/matrix/feature?'+urllib.urlencode(f_params, True)
    # biom
    abiom = async_rest_api(f_url+'&result_type=abundance', auth=token)
    ebiom = async_rest_api(f_url+'&result_type=evalue', auth=token)
    # matrix
    amatrix = sparse_to_dense(abiom['data'], abiom['shape'][0], abiom['shape'][1])
    ematrix = sparse_to_dense(ebiom['data'], ebiom['shape'][0], ebiom['shape'][1])
    # all md5s
    md5s = map(lambda x: x['id'], abiom['rows'])
    
    # get annotations for taxa
    if opts.top > 0:
        # get annotations for individual taxa
        for taxa in top_taxa:
            func_md5, func_acc = annotations_for_taxa(opts, md5s, [taxa])
            output_annotation(md5s, func_md5, func_acc, amatrix, ematrix, taxa)
        # get annotations for tail
        if opts.rest:
            func_md5, func_acc = annotations_for_taxa(opts, md5s, top_taxa, True)
            output_annotation(md5s, func_md5, func_acc, amatrix, ematrix, 'tail')
    else:
        # get annotations for all taxa
        func_md5, func_acc = annotations_for_taxa(opts, md5s, top_taxa)
        output_annotation(md5s, func_md5, func_acc, amatrix, ematrix, 'glob')
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
