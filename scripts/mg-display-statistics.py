#!/usr/bin/env python

import sys
import math
from operator import itemgetter
from optparse import OptionParser
from mglib.mglib import *
from mglib import aplotter

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
    mg-display-statistics --id "mgm4441680.3" --stat sequence

SEE ALSO
    -

AUTHORS
    %s
"""

def scale_histo(plot, width):
    axis = '|'+''.join([' ' for i in range(width-2)])+'|'
    buff = [' ' for i in range((width-6)/2)]
    scale = '0'+''.join(buff)+'bp'+''.join(buff)+str(width)
    plot.append(axis)
    plot.append(scale)
    return plot

def plot_histo(cols, data, height, width):
    if len(data) < width:
        width = len(data)
    plot = [['N' for i in range(width)] for j in range(height)]
    for pos, percents in enumerate(data[:width]):
        bps = []
        for i, per in enumerate(percents):
            num = int(per/5)
            for x in range(num):
                bps.append(cols[i])
        for row in range(len(plot)):
            try:
                plot[row][pos] = bps[row]
            except:
                pass
    out = [''.join(row) for row in plot]
    out = scale_histo(out, width)
    safe_print("\n".join(out)+"\n")

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--id", dest="id", default=None, help="KBase Metagenome ID")
    parser.add_option("", "--url", dest="url", default=API_URL, help="communities API url")
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")
    parser.add_option("", "--plot", dest="plot", action="store_true", default=False, help="display plot in ASCII art instead of table of numbers for: bp_profile, drisee, kmer, rarefaction, or taxa level")
    parser.add_option("", "--stat", dest="stat", default='sequence', help="type of stat to display, use keyword: 'sequence', 'bp_profile', 'drisee', 'kmer', 'rarefaction', or taxa level name, default is sequence")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if not opts.id:
        sys.stderr.write("ERROR: id required\n")
        return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # build call url
    url = opts.url+'/metagenome/'+opts.id+'?verbosity=stats'

    # retrieve / output data
    result = obj_from_url(url, auth=token)
    stats  = result['statistics']
    if opts.stat == 'sequence':
        for s in sorted(stats['sequence_stats'].iterkeys()):
            safe_print("%s\t%s\n" %(s, stats['sequence_stats'][s]))
    elif opts.stat == 'bp_profile':
        if not stats['qc']['bp_profile']['percents']['data']:
            sys.stderr.write("ERROR: %s has no bp_profile statistics\n"%opts.id)
            return 1
        if opts.plot:
            cols = stats['qc']['bp_profile']['percents']['columns'][1:5]
            data = map(lambda x: x[1:5], stats['qc']['bp_profile']['percents']['data'])
            plot_histo(cols, data, 20, 80)
        else:
            safe_print("\t".join(stats['qc']['bp_profile']['percents']['columns'])+"\n")
            for d in stats['qc']['bp_profile']['percents']['data']:
                safe_print("\t".join(map(str, d))+"\n")
    elif opts.stat == 'drisee':
        if not stats['qc']['drisee']['percents']['data']:
            sys.stderr.write("ERROR: %s has no drisee statistics\n"%opts.id)
            return 1
        if opts.plot:
            x, y = [], []
            for d in stats['qc']['drisee']['percents']['data']:
                x.append(d[0])
                y.append(d[7])
            aplotter.plot(x, y, output=sys.stdout, draw_axes=True, plot_slope=True, min_x=0, min_y=0)
        else:
            safe_print("\t".join(stats['qc']['drisee']['percents']['columns'])+"\n")                
            for d in stats['qc']['drisee']['percents']['data']:
                safe_print("\t".join(map(str, d))+"\n")
    elif opts.stat == 'kmer':
        if not stats['qc']['kmer']['15_mer']['data']:
            sys.stderr.write("ERROR: %s has no kmer statistics\n"%opts.id)
            return 1
        if opts.plot:
            x, y = [], []
            for d in stats['qc']['kmer']['15_mer']['data']:
                x.append( math.log(d[3], 10) )
                y.append( math.log(d[0], 10) )
            aplotter.plot(x, y, output=sys.stdout, draw_axes=True, plot_slope=True, min_x=0, min_y=0)
        else:
            safe_print("\t".join(stats['qc']['kmer']['15_mer']['columns'])+"\n")
            for d in stats['qc']['kmer']['15_mer']['data']:
                safe_print("\t".join(map(str, d))+"\n")
    elif opts.stat == 'rarefaction':
        if not stats['rarefaction']:
            sys.stderr.write("ERROR: %s has no rarefaction statistics\n"%opts.id)
            return 1
        if opts.plot:
            x, y = [], []
            for r in stats['rarefaction']:
                x.append(int(r[0]))
                y.append(float(r[1]))
            aplotter.plot(x, y, output=sys.stdout, draw_axes=True, plot_slope=True, min_x=0, min_y=0)
        else:
            safe_print("x\ty\n")
            for r in stats['rarefaction']:
                safe_print("%s\t%s\n" %(str(r[0]), str(r[1])))
    elif opts.stat in stats['taxonomy']:
        ranked = sorted(stats['taxonomy'][opts.stat], key=lambda x: (-int(x[1]), x[0]))
        if opts.plot:
            top = map(lambda x: int(x[1]), ranked)[:50]
            aplotter.plot(top, output=sys.stdout, draw_axes=True, plot_slope=False, min_x=0, min_y=0)
        else:
            for t in ranked:
                safe_print("%s\t%s\n" %(t[0], str(t[1])))
    else:
        sys.stderr.write("ERROR: invalid stat type\n")
        return 1
    
    return 0    

if __name__ == "__main__":
    sys.exit( main(sys.argv) )
