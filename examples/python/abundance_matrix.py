#!/usr/bin/env python
'''This script retrieves a metagenome_statistics data structure from the MG-RAST API and
plots a graph using data from the web interface'''

from __future__ import print_function
import sys
from optparse import OptionParser
from mglib.mglib import async_rest_api, sparse_to_dense, get_auth_token

DEBUG = 0
API_URL = "http://api.metagenomics.anl.gov/1"

if __name__ == '__main__':
    usage = "usage: %prog -i <input sequence file> -o <output file>"
    parser = OptionParser(usage)
    parser.add_option("-s", "--source", dest="source", default="RefSeq", help="Annotation source: RefSeq, GenBank, IMG, SEED, TrEMBL, SwissProt, PATRIC, KEG, RDP, Greengenes, LSU, SSU")
    parser.add_option("-g", "--grouplevel", dest="grouplevel", default="domain", help="Grouping level: strain, species, genus, family, order, class, phylum, domain / function, level1, level2, level3")
    parser.add_option("-i", "--hittype", dest="hittype", default="single", help="Hit type: all, single, lca")
    parser.add_option("-c", "--call", dest="call", default="organism", help="organism or function")
    parser.add_option("-d", "--identity", dest="identity", default=1, help="% identity threshold")
    parser.add_option("-e", "--evalue", dest="evalue", default="1", help="organism or function")
    parser.add_option("-t", "--type", dest="resulttype", default="abundance", help="Result type: abundnaance, evalue, identity, or length")
    parser.add_option("-n", "--ngth", dest="length", default="1", help="leNgth of hit")
#    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=True, help="Verbose [default off]")
    parser.add_option("-k", "--token", dest="token", type="str", help="Auth token")
    parser.add_option("-m", "--metagenomes", dest="metagenomes", default="mgm4447943.3,mgm4447102.3", type="str", help="Metagenome list")

    (opts, args) = parser.parse_args()
    key = get_auth_token(opts)
# assign parameters

    metagenomes = opts.metagenomes
    group_level = opts.grouplevel
    result_type = opts.resulttype
    source = opts.source
    evalue = opts.evalue
    length = opts.length
    identity = opts.identity
    hittype = opts.hittype
# construct API call
    base_url = API_URL + "/matrix/organism"
    if opts.call == "function" or opts.source == "SubSystems":
        base_url = API_URL + "/matrix/function"
    base_url = base_url + "?asynchronous=1&group_level=%s&result_type=%s&auth=%s&source=%s&evalue=%s&length=%s&identity=%s&hittype=%s&" % (group_level, result_type, key, source, evalue, length, identity, hittype)
    URI = base_url + "&".join(["id=%s" % m for m in metagenomes.split(",")])
    print(URI, file=sys.stderr)
    print("#"+ URI, file=sys.stdout)
# retrieve the data by sending at HTTP GET request to the MG-RAST API

    jsonstructure = async_rest_api(URI, auth=key)

# unpack and display the data table
    cols = [x["id"] for x in jsonstructure["columns"]]
    rows = [x["id"] for x in jsonstructure["rows"]]
    matrixtype = jsonstructure["type"]

    if matrixtype == "sparse":
        data = sparse_to_dense(jsonstructure["data"], len(rows), len(cols))
    else:
        data = jsonstructure["data"]

    if DEBUG:
        print(jsonstructure)
        print("COLS", cols)
        print("ROWS", rows)
        print("TYPE", matrixtype)
        print("DATA", data)
    h = data

    sys.stdout.write("Taxon\t")
    for j in range(0, len(cols)):
        sys.stdout.write(cols[j])
    sys.stdout.write("\n")
    for i in range(0, len(rows)):
        sys.stdout.write(rows[i])
        for j in range(0, len(cols)):
            sys.stdout.write("\t")
            try:
                sys.stdout.write(str(h[i][j]))
            except KeyError:
                sys.stdout.write("0")
        sys.stdout.write("\n")
