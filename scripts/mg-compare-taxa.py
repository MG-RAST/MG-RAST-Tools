#!/usr/bin/env python

import os
import sys
import json
import copy
from argparse import ArgumentParser
from mglib import get_auth_token, AUTH_LIST, VERSION, API_URL, urlencode, async_rest_api, merge_biom, obj_from_url, biom_to_tab

prehelp = """
NAME
    mg-compare-taxa

VERSION
    %s

SYNOPSIS
    mg-compare-taxa [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --ids <metagenome ids>, --level <taxon level>, --source <taxon datasource>, --filter_level <taxon level>, --filter_name <taxon name>, --intersect_source <function datasource>, --intersect_level <function level>, --intersect_name <function name>, --evalue <evalue negative exponent>, --identity <percent identity>, --length <alignment length>, --format <cv: 'text' or 'biom'> ]

DESCRIPTION
    Retrieve matrix of taxanomic abundance profiles for multiple metagenomes.
"""

posthelp = """
Output
    1. Tab-delimited table of taxanomic abundance profiles, metagenomes in columns and taxa in rows.
    2. BIOM format of taxanomic abundance profiles.

EXAMPLES
    mg-compare-taxa --ids "mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3" --level class --source RefSeq --format text --evalue 8

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_argument("--ids", dest="ids", default=None, help="comma seperated list or file of KBase Metagenome IDs")
    parser.add_argument("--url", dest="url", default=API_URL, help="communities API url")
    parser.add_argument("--user", dest="user", default=None, help="OAuth username")
    parser.add_argument("--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_argument("--token", dest="token", default=None, help="OAuth token")
    parser.add_argument("--level", dest="level", default='genus', help="taxon level to retrieve abundances for, default is genus")
    parser.add_argument("--source", dest="source", default='SEED', help="taxon datasource to filter results by, default is SEED")
    parser.add_argument("--hit_type", dest="hit_type", default='lca', help="Set of organisms to search results by, one of: all, single, lca")
    parser.add_argument("--filter_level", dest="filter_level", default=None, help="taxon level to filter by")
    parser.add_argument("--filter_name", dest="filter_name", default=None, help="taxon name to filter by, file or comma seperated list")
    parser.add_argument("--intersect_source", dest="intersect_source", default='Subsystems', help="function datasource for insersection, default is Subsystems")
    parser.add_argument("--intersect_level", dest="intersect_level", default=None, help="function level for insersection")
    parser.add_argument("--intersect_name", dest="intersect_name", default=None, help="function name(s) for insersection, file or comma seperated list")
    parser.add_argument("--output", dest="output", default='-', help="output: filename or stdout (-), default is stdout")
    parser.add_argument("--format", dest="format", default='biom', help="output format: 'text' for tabbed table, 'biom' for BIOM format, default is biom")
    parser.add_argument("--evalue", type=int, dest="evalue", default=15, help="negative exponent value for maximum e-value cutoff, default is 15")
    parser.add_argument("--identity", type=int, dest="identity", default=60, help="percent value for minimum %% identity cutoff, default is 60")
    parser.add_argument("--length", type=int, dest="length", default=15, help="value for minimum alignment length cutoff, default is 15")
    parser.add_argument("--hierarchy", action="store_true", dest="hierarchy", help="Don't use id, show hierarchy")
    parser.add_argument("--version", type=int, dest="version", default=1, help="M5NR annotation version to use, default is 1")
    parser.add_argument("--temp", dest="temp", default=None, help="filename to temporarly save biom output at each iteration")

    # get inputs
    opts = parser.parse_args()
    if not opts.ids:
        sys.stderr.write("ERROR: one or more ids required\n")
        return 1
    if (opts.filter_name and (not opts.filter_level)) or ((not opts.filter_name) and opts.filter_level):
        sys.stderr.write("ERROR: both --filter_level and --filter_name need to be used together\n")
        return 1
    if (opts.intersect_name and (not opts.intersect_level)) or ((not opts.intersect_name) and opts.intersect_level):
        sys.stderr.write("ERROR: both --intersect_level and --intersect_name need to be used together\n")
        return 1
    if opts.format not in ['text', 'biom']:
        sys.stderr.write("ERROR: invalid input format\n")
        return 1

    # get auth
    token = get_auth_token(opts)

    # build url
    id_list = []
    if os.path.isfile(opts.ids):
        id_str = open(opts.ids, 'r').read()
        try:
            id_obj = json.loads(id_str)
            if 'elements' in id_obj:
                id_list = id_obj['elements'].keys()
            elif 'members' in id_obj:
                id_list = map(lambda x: x['ID'], id_obj['members'])
        except:
            id_list = id_str.strip().split('\n')
    else:
        id_list = opts.ids.strip().split(',')
    params = [('group_level', opts.level),
              ('source', opts.source),
              ('hit_type', opts.hit_type),
              ('evalue', opts.evalue),
              ('identity', opts.identity),
              ('length', opts.length),
              ('version', opts.version),
              ('result_type', 'abundance'),
              ('asynchronous', '1')]
    if opts.intersect_level and opts.intersect_name:
        params.append(('filter_source', opts.intersect_source))
        params.append(('filter_level', opts.intersect_level))
        if os.path.isfile(opts.intersect_name):
            with open(opts.intersect_name) as file_:
                for f in file_:
                    params.append(('filter', f.strip()))
        else:
            for f in opts.intersect_name.strip().split(','):
                params.append(('filter', f))

    # retrieve data
    biom = None
    size = 50
    if len(id_list) > size:
        for i in range(0, len(id_list), size):
            sub_ids = id_list[i:i+size]
            cur_params = copy.deepcopy(params)
            for i in sub_ids:
                cur_params.append(('id', i))
            cur_url = opts.url+'/matrix/organism?'+urlencode(cur_params, True)
            cur_biom = async_rest_api(cur_url, auth=token)
            biom = merge_biom(biom, cur_biom)
            if opts.temp:
                json.dump(biom, open(opts.temp, 'w'))
    else:
        for i in id_list:
            params.append(('id', i))
        url = opts.url+'/matrix/organism?'+urlencode(params, True)
        biom = async_rest_api(url, auth=token)["data"]
        if opts.temp:
            json.dump(biom, open(opts.temp, 'w'))

    # get sub annotations
    sub_ann = set()
    if opts.filter_name and opts.filter_level:
        # get input filter list
        filter_list = []
        if os.path.isfile(opts.filter_name):
            with open(opts.filter_name) as file_:
                for f in file_:
                    filter_list.append(f.strip())
        else:
            for f in opts.filter_name.strip().split(','):
                filter_list.append(f)
        # annotation mapping from m5nr
        params = [('version', opts.version),
                  ('min_level', opts.level)]
        url = opts.url+'/m5nr/taxonomy?'+urlencode(params, True)
        data = obj_from_url(url)
        for ann in data['data']:
            if (opts.filter_level in ann) and (opts.level in ann) and (ann[opts.filter_level] in filter_list):
                sub_ann.add(ann[opts.level])

    # output data
    if (not opts.output) or (opts.output == '-'):
        out_hdl = sys.stdout
    else:
        out_hdl = open(opts.output, 'w')

    if opts.format == 'biom':
        out_hdl.write(json.dumps(biom)+"\n")
    else:
        biom_to_tab(biom, out_hdl, rows=sub_ann, use_id=not opts.hierarchy) 

    out_hdl.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
