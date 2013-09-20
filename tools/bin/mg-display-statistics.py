#!/usr/bin/env python

import sys
import urllib
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-display-statistics

VERSION
    %s

SYNOPSIS
    mg-display-statistics [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --id <metagenome id>, --stat <cv: 'sequence', 'bp_profile', 'drisee', 'kmer', 'rarefaction', taxa_level> ]

DESCRIPTION
    Retrieve statistical overview data for a metagenome.
"""

posthelp = """
Output
    Tab-delimited table of numbers (with text header). Output varies based on type of statistic requested.

EXAMPLES
    mg-display-statistics --id "kb|mg.287" --stat sequence

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--id", dest="id", default=None, help="KBase Metagenome ID")
    parser.add_option("", "--url", dest="url", default=API_URL, help="communities API url")
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")
    parser.add_option("", "--stat", dest="stat", default='sequence', help="type of stat to display, use keyword: 'sequence', 'bp_profile', 'drisee', 'kmer', 'rarefaction', or taxa level name, default is sequence")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if not opts.id:
        sys.stderr.write("ERROR: id required\n")
        return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # build call url
    if opts.id.startswith('kb|'):
        opts.id = kbid_to_mgid(opts.id)
    url = opts.url+'/metagenome/'+opts.id+'?verbosity=stats'

    # retrieve / output data
    result = obj_from_url(url, auth=token)
    stats  = result['statistics']
    if opts.stat == 'sequence':
        for s in sorted(stats['sequence_stats'].iterkeys()):
            sys.stdout.write("%s\t%s\n" %(s, stats['sequence_stats'][s]))
    elif opts.stat == 'bp_profile':
        if not stats['qc']['bp_profile']['percents']['data']:
            sys.stderr.write("ERROR: %s has no bp_profile statistics\n"%opts.id)
            return 1
        sys.stdout.write("\t".join(stats['qc']['bp_profile']['percents']['columns'])+"\n")
        for d in stats['qc']['bp_profile']['percents']['data']:
            sys.stdout.write("\t".join(map(str, d))+"\n")
    elif opts.stat == 'drisee':
        if not stats['qc']['drisee']['percents']['data']:
            sys.stderr.write("ERROR: %s has no drisee statistics\n"%opts.id)
            return 1
        sys.stdout.write("\t".join(stats['qc']['drisee']['percents']['columns'])+"\n")
        for d in stats['qc']['drisee']['percents']['data']:
            sys.stdout.write("\t".join(map(str, d))+"\n")
    elif opts.stat == 'kmer':
        if not stats['qc']['kmer']['15_mer']['data']:
            sys.stderr.write("ERROR: %s has no kmer statistics\n"%opts.id)
            return 1
        sys.stdout.write("\t".join(stats['qc']['kmer']['15_mer']['columns'])+"\n")
        for d in stats['qc']['kmer']['15_mer']['data']:
            sys.stdout.write("\t".join(map(str, d))+"\n")
    elif opts.stat == 'rarefaction':
        if not stats['rarefaction']:
            sys.stderr.write("ERROR: %s has no rarefaction statistics\n"%opts.id)
            return 1
        sys.stdout.write("x\ty\n")
        for r in stats['rarefaction']:
            sys.stdout.write("%s\t%s\n" %(str(r[0]), str(r[1])))
    elif opts.stat in stats['taxonomy']:
        for s in stats['taxonomy'][opts.stat]:
            sys.stdout.write("%s\t%s\n" %(s[0], str(s[1])))
    else:
        sys.stderr.write("ERROR: invalid stat type\n")
        return 1
    
    return 0    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
