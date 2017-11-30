import urllib

from mglib.mglib import obj_from_url, async_rest_api, get_auth_token
APIURL = "http://api.metagenomics.anl.gov/"

TESTAPI = "http://dunkirk.mcs.anl.gov/~paczian/MG-RAST/site/CGI/api.cgi/test?" # code=200&obj=\{%22test%22%3A%22ok%22\}"

def test_heartbeat():
    URI0 = APIURL + "heartbeat"   
    obj = obj_from_url(URI0)
    SERVICES = [ obj["requests"][1]["parameters"]["required"]["service"][1][i][0] for i in range(len( obj["requests"][1]["parameters"]["required"]["service"][1]))] 
    for service in SERVICES:
        URI = APIURL + "heartbeat/" + service
        obj_detail = obj_from_url(URI)
        assert obj_detail["status"] == 1, "Failed heartbeat on " + service
    return 1 

def test_async():
    URI = APIURL + '1/matrix/organism?id=mgm4653781.3&id=mgm4653783.3&id=mgm4653789.3&id=mgm4662211.3&id=mgm4662212.3&id=mgm4662235.3&id=mgm4662243.3&id=mgm4662299.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0&asynchronous=1'
#    'http://api.metagenomics.anl.gov/1/matrix/organism?id=mgm4653781.3&id=mgm4653783.3&id=mgm4653789.3&id=mgm4662211.3&id=mgm4662212.3&id=mgm4662235.3&id=mgm4662243.3&id=mgm4662299.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0'
    token = get_auth_token(None)
    response = async_rest_api(URI, auth=token)
    print(response)


def test_matrix_01():
    URI = APIURL + '/matrix/organism?id=mgm4440281.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0'
    obj = obj_from_url(URI)
    o = open("1.txt", "w")
    o.write(str(obj))
def test_matrix_02():
    URI = APIURL + '/matrix/organism?id=mgm4440282.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0'
    obj = obj_from_url(URI)
    o = open("2.txt", "w")
    o.write(str(obj))
def test_matrix_03():
    URI = APIURL + '/matrix/organism?id=mgm4440283.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0'
    obj = obj_from_url(URI)
    o = open("3.txt", "w")
    o.write(str(obj))
def test_matrix_04():
    URI = APIURL + '/matrix/organism?id=mgm4440284.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0'
    obj = obj_from_url(URI)
    o = open("4.txt", "w")
    o.write(str(obj))
    
def test_large_01():
    URI = APIURL + '/matrix/organism?group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0&id=mgm4510219.3'
    obj = obj_from_url(URI)
    o = open("5.txt", "w")
    o.write(str(obj))
def test_large_02():
    URI = APIURL + '/matrix/organism?group_level=phylum&source=RefSeq&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0&id=mgm4510219.3'
    obj = obj_from_url(URI)
    o = open("6.txt", "w")
    o.write(str(obj))
def test_large_03():
    URI = APIURL + '/matrix/organism?group_level=phylum&source=SEED&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0&id=mgm4510219.3'
    obj = obj_from_url(URI)
    o = open("7.txt", "w")
    o.write(str(obj))
