#!/usr/bin/env python

import sys
from collections import defaultdict
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-kegg2ss

VERSION
    %s

SYNOPSIS
    mg-kegg2ss [ --help, --input <input file or stdin>, --output <cv: 'text' or 'biom'> ]

DESCRIPTION
    Output metagenome annotations 
"""

posthelp = """
Output
    BIOM format of subsystems
    OR
    Tab-delimited list of annotations: feature list, subsystem function, abundance for function, avg evalue for function, organism

EXAMPLES
    mg-kegg2ss --input - --output text

SEE ALSO
    -

AUTHORS
    %s
"""

# get subsystems->roles and md5s per ko id
def ko2roles(opts, sshier, koid):
    ko_anno = obj_from_url(opts.url+'/m5nr/accession/'+koid+'?version=1&source=KO&limit=1000')
    ko_md5s = set( map(lambda x: x['md5'], ko_anno['data']) )
    if len(ko_md5s) == 0:
        return [], []
    ko_post = {'version': 1, 'source': 'Subsystems', 'data': list(ko_md5s), 'limit': 10000}
    ss_anno = obj_from_url(opts.url+'/m5nr/md5', data=json.dumps(ko_post, separators=(',',':')))
    roles   = set()
    for ss in ss_anno['data']:
        if ss['accession'] in sshier:
            roles.add( sshier[ss['accession']]['level4'] )
    return list(roles), list(ko_md5s)

# get fig ids per subsystem and roles
def role2figs(opts, role, md5s):
    post = {'version': 1, 'source': 'SEED', 'data': [role], 'md5s': md5s, 'exact': 1, 'limit': 10000}
    anno = obj_from_url(opts.url+'/m5nr/function', data=json.dumps(post, separators=(',',':')))
    fids = set( map(lambda x: x['accession'], anno['data']) )
    return list(fids)

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--id", dest="id", default=None, help="KBase Metagenome ID, required")
    parser.add_option("", "--url", dest="url", default=API_URL, help="communities API url")
    parser.add_option("", "--input", dest="input", default='-', help="input: filename or stdin (-), default is stdin")
    parser.add_option("", "--output", dest="output", default='text', help="output format: 'text' for tabbed table, 'biom' for BIOM format, default is text")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if (opts.input != '-') and (not os.path.isfile(opts.input)):
        sys.stderr.write("ERROR: input data missing\n")
        return 1
    if opts.output not in ['text', 'biom']:
        sys.stderr.write("ERROR: invalid output format\n")
        return 1
    
    # get biom
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        biom = json.loads(indata)
        rows, cols, matrix = biom_to_matrix(biom)
    except:
        sys.stderr.write("ERROR: unable to load input biom data\n")
        return 1
    
    # get SS hierarchy
    ss_hier = dict([ (x['accession'], x) for x in obj_from_url(opts.url+'m5nr/ontology?version=1&source=Subsystems')['data'] ])
    
    # biom KO -> SS
    ssrows = []
    ssmatrix = []
    for r, rid in enumerate(rows):
        roles, md5s = ko2roles(opts, ss_hier, rid)
        if not roles:
            continue
        for role in roles:
            fig_ids = role2figs(opts, role, md5s)
            print rid, role, len(fig_ids)
            ssrows.append({'id': role, 'metadata': {'accession': fig_ids}})
            ssmatrix.append(matrix[r])
    biom['matrix_type'] = 'sparse'
    biom['shape'][0] = len(ssrows)
    biom['rows'] = ssrows
    biom['data'] = ssmatrix
    return 0
    # output data
    if opts.output == 'biom':
        safe_print(json.dumps(biom)+"\n")
    elif opts.output == 'text':
        for r, row in enumerate(biom['rows']):
            # output: feature list, function, abundance for function, avg evalue for function, organism
            safe_print("%s\t%s\t%d\t%.2e\t%s\n" %(",".join(row['metadata']['accession']), row['id'], biom['data'][r][0], 0, 'glob'))
    else:
        sys.stderr.write("ERROR: invalid output type, use one of: text, biom\n")
        return 1
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
