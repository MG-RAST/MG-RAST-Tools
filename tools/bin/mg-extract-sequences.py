#!/usr/bin/env python

import sys
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-extract-sequences

VERSION
    %s

SYNOPSIS
    mg-extract-sequences [ --function <function name> ]

DESCRIPTION
    Retrieve annotated sequences from metagenomes filtered by function name and metadata.
"""

posthelp = """
Output
    Tab-delimited list of: m5nr id, dna sequence, semicolon seperated list of annotations, sequence id

EXAMPLES
    mg-extract-sequences --function "protease" --biome "marine"

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    
    parser.add_option("", "--url", dest="url", default=API_URL, help="API url")
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")

    parser.add_option("", "--function", dest="function", default=None, help="partial or full function string")

    parser.add_option("", "--level", dest="level", default=None, help="function level to filter by")
    parser.add_option("", "--source", dest="source", default='Subsystems', help="datasource to filter results by, default is Subsystems")
    parser.add_option("", "--evalue", dest="evalue", default=5, help="negative exponent value for maximum e-value cutoff, default is 5")
    parser.add_option("", "--identity", dest="identity", default=60, help="percent value for minimum % identity cutoff, default is 60")
    parser.add_option("", "--length", dest="length", default=15, help="value for minimum alignment length cutoff, default is 15")

    parser.add_option("", "--PI_firstname", dest="PI_firstname", default=None, help="principal investigator's first name")
    parser.add_option("", "--PI_lastname", dest="PI_lastname", default=None, help="principal investigator's last name")
    parser.add_option("", "--project_name", dest="project_name", default=None, help="name of project containing metagenome")
    parser.add_option("", "--project_id", dest="project_id", default=None, help="id of project containing metagenome")
    parser.add_option("", "--name", dest="name", default=None, help="name of metagenome")
    parser.add_option("", "--created", dest="created", default=None, help="time the metagenome was first created")
    parser.add_option("", "--status", dest="status", default="both", help="public, private or both, default is both")
    parser.add_option("", "--sequence_type", dest="sequence_type", default=None, help="sequencing type")
    parser.add_option("", "--seq_method", dest="seq_method", default=None, help="sequencing method")
    parser.add_option("", "--collection_date", dest="collection_date", default=None, help="date sample collected")
    parser.add_option("", "--country", dest="country", default=None, help="country where sample taken")
    parser.add_option("", "--latitude", dest="latitude", default=None, help="latitude where sample taken")
    parser.add_option("", "--longitude", dest="longitude", default=None, help="longitude where sample taken")
    parser.add_option("", "--location", dest="location", default=None, help="location where sample taken")
    parser.add_option("", "--feature", dest="feature", default=None, help="environmental feature, EnvO term")
    parser.add_option("", "--biome", dest="biome", default=None, help="environmental biome, EnvO term")
    parser.add_option("", "--env_package_type", dest="env_package_type", default=None, help="enviromental package of sample, GSC term")
    parser.add_option("", "--material", dest="material", default=None, help="environmental material, EnvO term")
    
    # get inputs
    (opts, args) = parser.parse_args()
    
    # get auth
    token = get_auth_token(opts)

    # build url for metagenome query
    params = []
    if opts.PI_firstname:
        params.append(('PI_firstname', opts.PI_firstname))
    if opts.PI_lastname:
        params.append(('PI_lastname', opts.PI_lastname))
    if opts.project_name:
        params.append(('project_name', opts.project_name))
    if opts.project_id:
        params.append(('project_id', opts.project_id))
    if opts.name:
        params.append(('name', opts.name))
    if opts.created:
        params.append(('created', opts.created))
    if opts.status:
        params.append(('status', opts.status))
    if opts.sequence_type:
        params.append(('sequence_type', opts.sequence_type))
    if opts.seq_method:
        params.append(('seq_method', opts.seq_method))
    if opts.collection_date:
        params.append(('collection_date', opts.collection_date))
    if opts.country:
        params.append(('country', opts.country))
    if opts.latitude:
        params.append(('latitude', opts.latitude))
    if opts.longitude:
        params.append(('longitude', opts.longitude))
    if opts.location:
        params.append(('location', opts.location))
    if opts.feature:
        params.append(('feature', opts.feature))
    if opts.biome:
        params.append(('biome', opts.biome))
    if opts.env_package_type:
        params.append(('env_package_type', opts.env_package_type))
    if opts.material:
        params.append(('material', opts.material))
    if opts.function:
        params.append(('function', opts.function))
    
    url = opts.url+'/metagenome?'+urllib.urlencode(params, True)
    retval = obj_from_url(url, auth=token)

    for i in retval['data']:
        id = i['id']
    
        # build url for sequences query
        params = [ ('source', opts.source),
                   ('evalue', opts.evalue),
                   ('identity', opts.identity),
                   ('length', opts.length) ]
        params.append(('type', 'function'))
        if opts.function:
            params.append(('filter', opts.function))
        if opts.level:
            params.append(('filter_level', opts.level))
        url = opts.url+'/annotation/sequence/'+id+'?'+urllib.urlencode(params, True)
    
        # output data
        sys.stdout.write('Results in '+id+":\n")
        stout_from_url(url, auth=token)
    
    return 0
    
if __name__ == "__main__":
    sys.exit( main(sys.argv) )
