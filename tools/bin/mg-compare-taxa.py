#!/usr/bin/env python

import os
import sys
import copy
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib import *

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
    mg-compare-taxa --ids "kb|mg.286,kb|mg.287,kb|mg.288,kb|mg.289" --level class --source RefSeq --format text --evalue 8

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--ids", dest="ids", default=None, help="comma seperated list or file of KBase Metagenome IDs")
    parser.add_option("", "--url", dest="url", default=API_URL, help="communities API url")
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")
    parser.add_option("", "--level", dest="level", default='species', help="taxon level to retrieve abundances for, default is species")
    parser.add_option("", "--source", dest="source", default='SEED', help="taxon datasource to filter results by, default is SEED")
    parser.add_option("", "--filter_level", dest="filter_level", default=None, help="taxon level to filter by")
    parser.add_option("", "--filter_name", dest="filter_name", default=None, help="taxon name to filter by, file or comma seperated list")
    parser.add_option("", "--intersect_source", dest="intersect_source", default='Subsystems', help="function datasource for insersection, default is Subsystems")
    parser.add_option("", "--intersect_level", dest="intersect_level", default=None, help="function level for insersection")
    parser.add_option("", "--intersect_name", dest="intersect_name", default=None, help="function name(s) for insersection, file or comma seperated list")
    parser.add_option("", "--format", dest="format", default='biom', help="output format: 'text' for tabbed table, 'biom' for BIOM format, default is biom")
    parser.add_option("", "--evalue", type="int", dest="evalue", default=5, help="negative exponent value for maximum e-value cutoff, default is 5")
    parser.add_option("", "--identity", type="int", dest="identity", default=60, help="percent value for minimum % identity cutoff, default is 60")
    parser.add_option("", "--length", type="int", dest="length", default=15, help="value for minimum alignment length cutoff, default is 15")
    parser.add_option("", "--temp", dest="temp", default=None, help="filename to temporarly save biom output at each iteration")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if not opts.ids:
        sys.stderr.write("ERROR: one or more ids required\n")
        return 1
    if (opts.filter_name and (not opts.filter_level)) or ((not opts.filter_name) and opts.filter_level):
        sys.stderr.write("ERROR: both --filter_level and --filter_name need to be used together\n")
        return 1
    if (opts.intersect_name and (not opts.intersect_level)) or ((not opts.intersect_name) and opts.intersect_level):
        sys.stderr.write("ERROR: both --intersect_level and --intersect_name need to be used together\n")
        return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # build url
    id_list = []
    if os.path.isfile(opts.ids):
        id_str = open(opts.ids,'r').read()
        try:
            id_obj  = json.loads(id_str)
            if 'elements' in id_obj:
                id_list = kbids_to_mgids( id_obj['elements'].keys() )
            elif 'members' in id_obj:
                id_list = kbids_to_mgids( map(lambda x: x['ID'], id_obj['members']) )
        except:
            id_list = kbids_to_mgids( id_str.strip().split('\n') )
    else:
        id_list = kbids_to_mgids( opts.ids.strip().split(',') )
    params = [ ('group_level', opts.level), 
               ('source', opts.source),
               ('evalue', opts.evalue),
               ('identity', opts.identity),
               ('length', opts.length),
               ('result_type', 'abundance'),
               ('asynchronous', '1') ]
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
        for i in xrange(0, len(id_list), size):
            sub_ids = id_list[i:i+size]
            cur_params = copy.deepcopy(params)
            for i in sub_ids:
                cur_params.append(('id', i))
            cur_url  = opts.url+'/matrix/organism?'+urllib.urlencode(cur_params, True)
            cur_biom = async_rest_api(cur_url, auth=token)
            biom = merge_biom(biom, cur_biom)
            if opts.temp:
                json.dump(biom, open(opts.temp, 'w'))
    else:
        for i in id_list:
            params.append(('id', i))
        url = opts.url+'/matrix/organism?'+urllib.urlencode(params, True)
        biom = async_rest_api(url, auth=token)
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
        params = [ ('version', '1'),
                   ('min_level', opts.level) ]
        url = opts.url+'/m5nr/taxonomy?'+urllib.urlencode(params, True)
        data = obj_from_url(url)
        for ann in data['data']:
            if (opts.filter_level in ann) and (opts.level in ann) and (ann[opts.filter_level] in filter_list):
                sub_ann.add(ann[opts.level])
    
    # output data
    if opts.format == 'biom':
        safe_print(json.dumps(biom)+"\n")
    elif opts.format == 'text':
        biom_to_tab(biom, sys.stdout, rows=sub_ann)
    else:
        sys.stderr.write("ERROR: invalid format type, use one of: text, biom\n")
        return 1
    
    return 0
    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
