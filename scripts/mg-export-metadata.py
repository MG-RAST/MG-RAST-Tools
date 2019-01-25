#!/usr/bin/env python

from __future__ import print_function

import sys
from argparse import ArgumentParser
import xlsxwriter

from mglib import VERSION, get_auth_token, AUTH_LIST, obj_from_url

prehelp = """
NAME
    mg-export-metadata.py

VERSION
    %s

SYNOPSIS
    mg-export-metadata [ --help] --project <project id>

DESCRIPTION
    Retrieve metadata for a metagenome.
"""

posthelp = """
Output
    excel file named "mgpXXXX-export.xlsx"

EXAMPLES
    mg-export-metadata.py --project mgp128

SEE ALSO
    -

AUTHORS
    %s
"""

def get_project_keys(meta):
    keys = set()
    for key in meta["data"].keys():
        keys.add(key)
    if "project_name" in keys:  keys.remove("project_name")
    return(["project_name"] + list(keys))

def get_sample_keys(meta):
    keys = set()
    for sample in meta["samples"]:
        for key in sample["data"].keys():
            keys.add(key)
    if "sample_name" in keys:  keys.remove("sample_name")
    return(["sample_name"] + list(keys))

def get_library_keys(meta):
    keys = set()
    for sample in meta["samples"]:
        for lib in sample["libraries"]:
            for key in lib["data"].keys():
                keys.add(key)
    keys.remove("sample_name")
    return(["sample_name"]+list(keys))
def get_eps(meta):
    eps = set()
    for sample in meta["samples"]:
        if "envPackage" in sample.keys():
            eps.add(sample["envPackage"]["type"])
    return(list(eps))

def get_ep_keys(meta, eps):
    epkeys = {ep: set() for ep in eps}
    for sample in meta["samples"]:
        ep = sample["envPackage"]["type"]
        for key in sample["envPackage"]["data"].keys():
            epkeys[ep].add(key)
    epkeysl = {}
    for ep in eps:
        epkeys[ep].remove("sample_name")
        epkeysl[ep] = ["sample_name"] + list(epkeys[ep])
    return(epkeysl)

def write_worksheet_value(worksheet, r, c, v, f):
#        write_worksheet_value(worksheet, row, col, value, fmt)
    if f == "text" or f == "ontology" or f == "select" or f == "timezone" or v == "":
        worksheet.write_string(r, c, v)
    elif f == "float" or f == "coordinate" or f == "int":
        worksheet.write_number(r, c, float(v))
    elif f == "date":
        worksheet.write_string(r, c, v)
    elif f == "time":
        worksheet.write_string(r, c, v)
    else:
        print("warning, falllback for format ", f)
        worksheet.write_string(r, c, v)
    return

def main(args):
    ArgumentParser.format_description = lambda self, formatter: self.description
    ArgumentParser.format_epilog = lambda self, formatter: self.epilog
    parser = ArgumentParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_argument("--project", dest="project", default=None, help="project ID")

    # get inputs
    opts = parser.parse_args()
    if not opts.project or opts.project[0:3] != "mgp":
        sys.stderr.write("ERROR: a project id is required\n")
        return 1
    # get auth
    PROJECT = opts.project

    TOKEN = get_auth_token(opts)

    # export metadata

    outfile = PROJECT + "-export.xlsx"
#
    k = obj_from_url("http://api.mg-rast.org/metadata/export/{project}?verbosity=full".format(project=PROJECT), auth=TOKEN)
    metadata = k # json.loads(open(infile).read())

    workbook = xlsxwriter.Workbook(outfile)
    print("Creating", outfile)
    worksheet = {}
    worksheet["README"] = workbook.add_worksheet("README")
    row = 0
    for i in range(10):
        worksheet["README"].write_number(row, 0, i)
        row += 1

    worksheet["project"] = workbook.add_worksheet("project")
    project_keys = get_project_keys(metadata)
    col = 0
    for l in project_keys:
        value = metadata["data"][l]["value"]
        definition = metadata["data"][l]["definition"]
        worksheet["project"].write_string(0, col, l)
        worksheet["project"].write_string(1, col, definition)
        worksheet["project"].write_string(2, col, value)
        col += 1

    worksheet["sample"] = workbook.add_worksheet("sample")

    samplekeys = get_sample_keys(metadata)

    col = 0
    row = 2
    for sample in metadata["samples"]:
        for l in samplekeys:
            if l in sample["data"].keys():
                value = sample["data"][l]["value"]
                definition = sample["data"][l]["definition"]
                fmt = sample["data"][l]["type"]
                worksheet["sample"].write_string(0, col, l)
                worksheet["sample"].write_string(1, col, definition)
                write_worksheet_value(worksheet["sample"], row, col, value, fmt)
            col += 1
        col = 0
        row += 1
    try:
        librarytype = metadata["samples"][0]["libraries"][0]["data"]["investigation_type"]["value"]
    except IndexError:
        sys.exit("This metadata bundle does not have any libraries")

    worksheet["library"] = workbook.add_worksheet("library "+librarytype)

    libkeys = get_library_keys(metadata)
    col = 0
    row = 2
    for sample in metadata["samples"]:
        for l in libkeys:
            if l in sample["libraries"][0]["data"].keys():
                value = sample["libraries"][0]["data"][l]["value"]
                definition = sample["libraries"][0]["data"][l]["definition"]
                fmt = sample["libraries"][0]["data"][l]["type"]
                worksheet["library"].write_string(0, col, l)
                worksheet["library"].write_string(1, col, definition)
                write_worksheet_value(worksheet["library"], row, col, value, fmt)
            col += 1
        col = 0
        row += 1

    eps = get_eps(metadata)
    print("eps", " ".join(eps))
    epcol = {}
    eprow = {}
    for ep in eps:
        worksheet[ep] = workbook.add_worksheet("ep " + ep)
        epcol[ep] = 0
        eprow[ep] = 2
    epkeys = get_ep_keys(metadata, eps)
    for sample in metadata["samples"]:
        ep = sample["envPackage"]["type"]
        for l in epkeys[ep]:
            try:
                value = sample["envPackage"]["data"][l]["value"]
                definition = sample["envPackage"]["data"][l]["definition"]
                fmt = sample["envPackage"]["data"][l]["type"]
            except KeyError:
                value = "" ; definition = ""; fmt = "string"

            worksheet[ep].write_string(0, epcol[ep], l)
            worksheet[ep].write_string(1, epcol[ep], definition)
            write_worksheet_value(worksheet[ep], eprow[ep], epcol[ep], value, fmt)
            epcol[ep] += 1
        epcol[ep] = 0
        eprow[ep] += 1

    workbook.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
