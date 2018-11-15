#!/usr/bin/env python
'''This script retrieves a metagenome_statistics data structure from the MG-RAST API and
plots a graph using data from the web interface'''

from __future__ import print_function
import sys
from optparse import OptionParser
from mglib import async_rest_api, get_auth_token, API_URL

DEBUG = 0


if __name__ == '__main__':
    usage = "usage: %prog -i <input sequence file> -o <output file>"
    parser = OptionParser(usage)
    parser.add_option("-s", "--source", dest="source", default="RefSeq", help="Annotation source: RefSeq, GenBank, IMG, SEED, TrEMBL, SwissProt, PATRIC, KEG, RDP, Greengenes, LSU, SSU")
    parser.add_option("-g", "--grouplevel", dest="grouplevel", default="domain", help="Grouping level: strain, species, genus, family, order, class, phylum, domain / function, level1, level2, level3")
    parser.add_option("-i", "--hittype", dest="hittype", default="single", help="Hit type: all, single, lca")
    parser.add_option("-c", "--call", dest="call", default="organism", help="organism or function")
    parser.add_option("-e", "--evalue", dest="evalue", default="1", help="organism or function")
    parser.add_option("-t", "--type", dest="resulttype", default="abundance", help="Result type: abundnaance, evalue, identity, or length")
    parser.add_option("-n", "--ngth", dest="length", default="15", help="leNgth of hit")
#    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=True, help="Verbose [default off]")
    parser.add_option("-k", "--token", dest="token", type="str", help="Auth token")
    parser.add_option("-m", "--metagenomes", dest="metagenomes", default="mgm4447943.3", type="str", help="Metagenome list")

    (opts, args) = parser.parse_args()
    key = get_auth_token(opts)
# assign parameters

    metagenomes = opts.metagenomes
    group_level = opts.grouplevel
    result_type = opts.resulttype
    source = opts.source
    evalue = opts.evalue

# construct API call
    base_url = API_URL + "/profile/{}".format(metagenomes)
    base_url = base_url + "?asynchronous=1&group_level=%s&result_type=%s&auth=%s&source=%s&evalue=%s&" % (group_level, result_type, key, source, evalue)
    URI = base_url + "&".join(["id=%s" % m for m in metagenomes.split(",")])
    URI = base_url 
    print(URI, file=sys.stderr)
# retrieve the data by sending at HTTP GET request to the MG-RAST API

    jsonstructure = async_rest_api(URI, auth=key)
    jsondata = jsonstructure["data"]
# unpack and display the data table
#    rows = [x["id"] for x in jsondata["rows"]]

    data = jsondata # ["data"]

    if DEBUG:
        print(jsonstructure)
        print("DATA", data)
    h = data

    for i in range(0, len(data)):
        sys.stdout.write("\t".join([str(s) for s in h[i]]))
        sys.stdout.write("\n")
