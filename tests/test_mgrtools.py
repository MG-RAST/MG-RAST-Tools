from __future__ import print_function

import pytest
#import mglib

from subprocess import Popen, PIPE
import subprocess
import sys, os 

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

def runme(command, workingdir=".", fail_ok=False):
    cwd = os.getcwd()
# We replace stdout and standard error here
#    oldout, olderr = sys.stdout, sys.stderr
#    sys.stdout = StringIO()
#    sys.stderr = StringIO()
    os.chdir(workingdir)  

    try: 
        p=subprocess.Popen(command.split(" "), stdout=PIPE, stderr=PIPE)
    except SystemExit as err:
        p = err.code
    out, err = p.communicate()
    status = p.returncode
    # sys.stdout.getvalue(), sys.stderr.getvalue()
    if status != 0 and not fail_ok:
        print(out)
        print(err)
        assert False, (status, out, err)

# Now undo all the renamed streams
#    sys.stdout, sys.stderr = oldout, olderr
    os.chdir(cwd)  
    return status, out, err


def test_always_succeeds():
     pass

def test_mginbox_help():
    stat, out, err = runme('mg-inbox.py -h')
    assert 'DESCRIPTION' in out
 
def test_mg_biom2metadata_help():
    stat, out, err = runme('mg-biom2metadata -h')
    assert 'DESCRIPTION' in out

def test_mg_biom2taxa_help():
    stat, out, err = runme('mg-biom2taxa -h')
    assert 'DESCRIPTION' in out

def test_mg_upload2shock_help():
    stat, out, err = runme('mg-upload2shock.py -h')
    assert 'DESCRIPTION' in out

binscripts = ['mg-abundant-functions.py',
'mg-abundant-taxa.py',
'mg-biom-merge.py',
'mg-biom-view.py',
'mg-changing-annotation.py',
'mg-compare-alpha-diversity.py',
'mg-compare-boxplot-plot.py',
'mg-compare-functions.py',
'mg-compare-heatmap-plot.py',
'mg-compare-heatmap.py',
'mg-compare-normalize.py',
'mg-compare-pcoa-plot.py',
'mg-compare-pcoa.py',
'mg-compare-taxa.py',
'mg-correlate-metadata.py',
'mg-display-metadata.py',
'mg-display-statistics.py',
'mg-download.py',
'mg-extract-sequences.py',
'mg-get-annotation-set.py',
'mg-get-sequences-for-function.py',
'mg-get-sequences-for-taxon.py',
'mg-get-similarity-for-function.py',
'mg-get-similarity-for-taxon.py',
'mg-group-significance.py',
'mg-inbox.py',
'mg-kegg2ss.py',
'mg-retrieve-uniprot.py',
'mg-search-metagenomes.py',
'mg-select-significance.py',
'mg-stable-annotation.py',
'mg-submit.py',
'mg-upload2ws.py' ]

def test_binscripts_help():
    for binscript in binscripts:
          print("Invoking " + binscript+" -h") 
          stat, out, err = runme(binscript + " -h") 
          assert 'DESCRIPTION' in out

def test_jsonviewer():
    s = '''echo '{"a": {"b": {"c": [1, 2, 3, 4, 5]}}, "x": ["y", "z"], "foo": "bar"}' | jsonviewer'''
    stat, out, err = runme(s) 
    s2 = '''echo '{"a": {"b": {"c": [1, 2, 3, 4, 5]}}, "x": ["y", "z"], "foo": "bar"}' | jsonviewer --value 'a.b.c' --json'''
    stat, out, err = runme(s2) 

def test_mg_abundant_functions():
    s = '''mg-abundant-functions.py --id mgm4441680.3 --level level3 --source Subsystems --top 20 --evalue 8'''
    stat, out, err = runme(s) 

def test_mg_abundant_taxa():
    s = '''mg-abundant-taxa.py --id mgm4441680.3 --level genus --source RefSeq --top 20 --evalue 8'''
    stat, out, err = runme(s) 

@pytest.mark.huge
def test_mg_compare_taxa():
    s = '''mg-compare-taxa.py --ids mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3 --level class --source RefSeq --format text | mg-changing-annotation --input - --format text --groups {"group1":["mgm4441679.3","mgm4441680.3"],"group2":["mgm4441681.3","mgm4441682.3"]} --top 5 --stat_test Kruskal-Wallis'''
    stat, out, err = runme(s) 

@pytest.mark.huge
def test_mg_compare_alpha_diversity():
    s= '''mg-compare-alpha-diversity.py --ids mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3 --level class --source RefSeq'''
    stat, out, err = runme(s) 

def test_mg_compare_functions():
    s='''mg-compare-functions.py --ids mgm4441679.3,mgm4441680.3,mgm4441681.3,mgm4441682.3 --level level2 --source KO --format text --evalue 8'''
    stat, out, err = runme(s) 

def test_mg_display_statistics():
    s='''mg-display-statistics.py --id mgm4441680.3 --stat sequence'''
    stat, out, err = runme(s) 
  
def test_mg_download():
    s='''mg-download.py --metagenome mgm4441680.3 --list''' 
    stat, out, err = runme(s) 

#def test_mg_extract_sequences():
#    s='''mg-extract-sequences.py --function protease --biome marine'''
#    stat, out, err = runme(s) 

def test_mg_get_annotation_set():
    s='''mg-get-annotation-set.py --id mgm4441680.3 --top 5 --level genus --source SEED'''
    stat, out, err = runme(s) 
    assert stat == 0

def test_mg_get_sequences_for_function():
    s='''mg-get-sequences-for-function.py --id mgm4441680.3 --name Central\ carbohydrate\ metabolism --level level2 --source Subsystems --evalue 10'''
    stat, out, err = runme(s) 
    assert stat == 0

def test_mg_get_sequences_for_taxon():
    s='''mg-get-sequences-for-taxon.py --id mgm4441680.3 --name Lachnospiraceae --level family --source RefSeq --evalue 8'''
    stat, out, err = runme(s) 
    assert stat == 0

def test_mg_get_similarity_for_taxon():
    s='''mg-get-similarity-for-function.py --id mgm4441680.3 --name Central\ carbohydrate\ metabolism --level level2 --source Subsystems --evalue 10'''
    stat, out, err = runme(s) 
    assert stat == 0
def test_mg_inbox_view():
    s='''mg-inbox.py view all'''
    stat, out, err = runme(s) 
    assert stat == 0
def test_mb_kegg2ss():
    s = '''mg-kegg2ss.py --input - --output text'''
    stat, out, err = runme(s) 
    assert stat == 0
def test_mg_retrieve_uniprot():
    s='''mg-retrieve-uniprot.py --md5 ffc62262a18b38671c3e337150ef535f --source SwissProt'''
    stat, out, err = runme(s) 
    assert stat == 0
def test_mg_search_metagenomes(): 
    s='''mg-search-metagenomes.py --help'''
    stat, out, err = runme(s) 
    assert stat == 0
def test_mg_submit():
    s='''mg-submit.py list'''
    stat, out, err = runme(s) 
    assert stat == 0

@pytest.mark.known_failing
def test_known_failing():
    assert False  # This should not normally run
