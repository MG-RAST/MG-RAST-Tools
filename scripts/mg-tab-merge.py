#!/usr/bin/env python

import os
import sys
import json
from argparse import ArgumentParser
from mglib import merge_biom, AUTH_LIST, VERSION, safe_print

prehelp = """
NAME
    mg-tab-merge

VERSION
    %s

SYNOPSIS
    mg-biom-merge [ --help --retain_dup_ids ] biom1 biom2 [ biom3 biom4 ... ]

DESCRIPTION
    Tool to merge two or more profiles in tab format (output from mg-biom2tag)
"""

posthelp = """
Input
    Two or more profile files in tab format

Output
    Merged tab to stdout

EXAMPLES
    mg-tab-merge --help

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_argument('profiles', metavar='N', type=str, nargs='+',
                    help='list of profiles in json')
    parser.add_argument("--retain_dup_ids", dest="retain_dups", action="store_true", default=False, help="append input number to duplicate input ID's rather than discarding duplicates, default is false")

    # get inputs
    opts = parser.parse_args()
    if len(args) < 2:
        sys.stderr.write("ERROR: must have at least 2 file inputs\n")
        return 1
    for f in args:
        if not os.path.isfile(f):
            sys.stderr.write("ERROR: %s is not a valid file\n")
            return 1
   


    init_row = [0 for x in range( len(opts.profiles) )]

    header = []
    subsystem2abundance = {}
    column = 0

    for profile in opts.profiles :
        header.append(profile)

        with open(profile, 'r') as p :
            for line in p :
                row = line.strip().split("\t")

                # get subsystem levels - not generic 
                levels = row[5:9]
   
                if levels[0] not in subsystem2abundance :
                    subsystem2abundance[levels[0]] = {}
                if levels[1] not in subsystem2abundance[levels[0]] :
                    subsystem2abundance[levels[0]][levels[1]] = {}
                if levels[2] not in subsystem2abundance[levels[0]][levels[1]] :
                    subsystem2abundance[levels[0]][levels[1]][levels[2]] = {}
                if levels[3] not in subsystem2abundance[levels[0]][levels[1]][levels[2]] :
                    subsystem2abundance[levels[0]][levels[1]][levels[2]][levels[3]] =  [0 for x in range( len(opts.profiles) )]

    
                subsystem2abundance[levels[0]][levels[1]][levels[2]][levels[3]][column] += int(row[1])
                
        column += 1

    # print 
    i = 0
    print( '', '' , '' , header)
    for l1 in subsystem2abundance :
        for l2 in subsystem2abundance[l1] :
            for l3 in subsystem2abundance[l1][l2] :
                abundances = init_row
                for l4 in subsystem2abundance[l1][l2][l3] :
                    for col , value in enumerate(subsystem2abundance[l1][l2][l3][l4]) :
                        abundances[col] += value
                    # print level4
                    # print( "\t".join( 
                    #     map( 
                    #         lambda x : str(x), 
                    #         [l1, l2, l3 , l4] + subsystem2abundance[l1][l2][l3][l4] 
                    #         )
                    #     )
                    # )

                print up to level3
                print( "\t".join( 
                    map( 
                        lambda x : str(x), 
                        [l1, l2, l3] + abundances 
                        )
                    )
                )

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
