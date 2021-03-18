#!/usr/bin/env python

import os
import sys
import json
from argparse import ArgumentParser
from mglib import biom_to_matrix, AUTH_LIST, VERSION
from array import array 


prehelp = """
NAME
    mg-biom2tab

VERSION
    %s

SYNOPSIS
    mg-biom2tab [ --help, --input <input file or stdin>, --output <output file or stdout>, --row_start <integer>, --row_end <integer>, --col_start <integer>, --col_end <integer>, --stats <boolean> ]

DESCRIPTION
    Tool to view slice of BIOM file as table with row and column ids
"""

posthelp = """
Input
    BIOM file

Output
    Tab-delimited table of BIOM sub-selection

EXAMPLES
    mg-biom2tab --help

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_argument("-i", "--input", dest="input", default='-', help="input: filename or stdin (-), default is stdin")
    parser.add_argument("-o", "--output", dest="output", default='-', help="output: filename or stdin (-), default is stdout")
    parser.add_argument("-m", "--mapping", dest="mapping", default='-', help="mapping: file containing taxonomy or other classifications")

    
    # get inputs
    opts = parser.parse_args()
    if (opts.input != '-') and (not os.path.isfile(opts.input)):
        sys.stderr.write("ERROR: input data missing\n")
        return 1

    if (not opts.output) or (opts.output == '-'):
        out_hdl = sys.stdout
    else:
        out_hdl = open(opts.output, 'w')

    # parse inputs
    try:
        indata = sys.stdin.read() if opts.input == '-' else open(opts.input, 'r').read()
        try:
            biom = json.loads(indata)
        except:
            sys.stderr.write("ERROR: input BIOM data not correct format\n")
            return 1
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1
    

    try:
        mappingdata =  open(opts.mapping, 'r').read()
        try:
            ontology = json.loads(mappingdata)
        except:
            sys.stderr.write("ERROR: input BIOM data not correct format\n")
            return 1
    except:
        sys.stderr.write("ERROR: unable to load input data\n")
        return 1

    id2o = {}
    for i in ontology['data'] :
        # id2o['i'] = "\t".join([ i['level1'] , i['level3'] ,i['level3'] ,i['level4'] ])
        id2o[i['accession']] = [ i['level1'] , i['level2'] if 'level2' in i else i['level1'] + " (level 1)" ,i['level3'] ,i['level4'] ]

    # for p in [ 'size' , 'id' , 'parameters'] :
    #     print("{}\t{}".format( p , biom[p]) )

    for r in biom['data']['data'] :
        pos = None 
        if r[5] is not None :
            pos = 5
        else:
             pos = 6

       
        # o = r[0:5]
        # o.append("a")
        # print(type(o))
        # print(o)

        for c in r[pos] :
            out = r[0:5] 
            h = [ 'unknown']
            if c in id2o :
                h = id2o[c]
            else :
                h.append(c)
            out.append( h )
            print("\t".join( map( lambda x : str(x) , out )  ) )
    
    # # output data
    # try:
    #     sub_rows = rows[row_start:row_end]
    #     out_hdl.write("\t%s\n" %"\t".join(cols[col_start:col_end]))
    #     for i, d in enumerate(data[row_start:row_end]):
    #         out_hdl.write("%s\t%s\n" %(sub_rows[i], "\t".join(map(str, d[col_start:col_end]))))
    #     out_hdl.close()
    # except:
    #     sys.stderr.write("ERROR: unable to sub-select BIOM, inputted positions are out of bounds\n")
    #     return 1
    # return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
