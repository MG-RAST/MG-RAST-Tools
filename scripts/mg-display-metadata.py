#!/usr/bin/env python

import sys
from argparse import ArgumentParser
from mglib import AUTH_LIST, VERSION, API_URL, get_auth_token, obj_from_url, safe_print

prehelp = """
NAME
    mg-display-metadata

VERSION
    %s

SYNOPSIS
    mg-display-metadata [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --id <metagenome id>, --verbosity <cv: 'mixs', 'full'> ]

DESCRIPTION
    Retrieve metadata for a metagenome.
"""

posthelp = """
Output
    Tab-delimited table of metadata key-value pairs, either minimal or full metadata.

EXAMPLES
    mg-display-metadata --id "mgm4441680.3" --verbosity full

SEE ALSO
    -

AUTHORS
    %s
"""

def main(args):
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_argument("--id", dest="id", default=None, help="KBase Metagenome ID")
    parser.add_argument("--url", dest="url", default=API_URL, help="communities API url")
    parser.add_argument("--user", dest="user", default=None, help="OAuth username")
    parser.add_argument("--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_argument("--token", dest="token", default=None, help="OAuth token")
    parser.add_argument("--verbosity", dest="verbosity", default='mixs', help="amount of metadata to display. use keyword 'mixs' for GSC MIxS metadata, use keyword 'full' for all GSC metadata, default is mixs")
    
    # get inputs
    opts = parser.parse_args()
    if not opts.id:
        sys.stderr.write("ERROR: id required\n")
        return 1
    
    # get auth
    token = get_auth_token(opts)
    
    # build call url
    verb = opts.verbosity if opts.verbosity == 'mixs' else 'metadata'
    url  = opts.url+'/metagenome/'+opts.id+'?verbosity='+verb

    # retrieve / output data
    result = obj_from_url(url, auth=token)
    if opts.verbosity == 'mixs':
        for r in sorted(result.keys()):
            if r not in ['project', 'library', 'sample']:
                safe_print("%s\t%s\n" %(r, result[r]))
    elif opts.verbosity == 'full':
        md = result['metadata']
        safe_print("category\tlabel\tvalue\n")
        if ('project' in md) and md['project']['data']:
            for p in sorted(md['project']['data'].keys()):
                safe_print("project\t%s\t%s\n" %(p, md['project']['data'][p]))
        if ('sample' in md) and md['sample']['data']:
            for s in sorted(md['sample']['data'].keys()):
                safe_print("sample\t%s\t%s\n" %(s, md['sample']['data'][s]))
        if ('library' in md) and ('type' in md['library']) and md['library']['data']:
            for l in sorted(md['library']['data'].keys()):
                safe_print("library: %s\t%s\t%s\n" %(md['library']['type'], l, md['library']['data'][l]))
        if ('env_package' in md) and ('type' in md['env_package']) and md['env_package']['data']:
            for e in sorted(md['env_package']['data'].keys()):
                safe_print("env package: %s\t%s\t%s\n" %(md['env_package']['type'], e, md['env_package']['data'][e]))
    else:
        sys.stderr.write("ERROR: invalid verbosity type\n")
        return 1
    
    return 0
    

if __name__ == "__main__":
    sys.exit(main(sys.argv))
