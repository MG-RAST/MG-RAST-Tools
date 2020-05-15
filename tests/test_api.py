#!/usr/bin/env python

import os

from mglib import obj_from_url, async_rest_api, get_auth_token, API_URL

def test_nonexist():
    URI = API_URL + '/matrix/organism?id=mgm4454394.3'  # mgm4454394.3 is deleted
    try:
        response = async_rest_api(URI, auth="")
        pass
    except SystemExit:
        pass

def test_500():
    URI = API_URL + '/nonexistentapicall'
    try:
        response = async_rest_api(URI, auth="")
        assert False
    except SystemExit:
        pass

def test_private():
    URI = API_URL + '/matrix/organism?id=mgm4454266.3'  # mgm4454266.3 is private
    try:
        response = async_rest_api(URI, auth="")
        assert False
    except SystemExit:
        pass

def test_badkey():
    URI = API_URL + '/matrix/organism?id=mgm4454266.3'  # mgm4454266.3 is private
    try:
        response = async_rest_api(URI, auth="ABCDEFGThisIsOneNoGoodKey")
        assert False
    except SystemExit:
        pass

def test_heartbeat():
    URI0 = API_URL + "heartbeat"
    obj = obj_from_url(URI0)
    SERVICES = [obj["requests"][1]["parameters"]["required"]["service"][1][i][0] for i in range(len(obj["requests"][1]["parameters"]["required"]["service"][1]))]
    for service in SERVICES:
        URI = API_URL + "heartbeat/" + service
        obj_detail = obj_from_url(URI)
        assert obj_detail["status"] == 1, "Failed heartbeat on " + service
    return 1

def test_async_matrix3():
    URI = API_URL + '1/matrix/organism?id=mgm4653781.3&id=mgm4653783.3&id=mgm4653789.3&id=mgm4662211.3&id=mgm4662212.3&id=mgm4662235.3&id=mgm4662210.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0&asynchronous=1'  # takes too long??
    URI = API_URL + '/matrix/organism?id=mgm4447943.3&id=mgm4447192.3&id=mgm4447102.3&group_level=family&source=RefSeq&evalue=15'
    token = get_auth_token(None)
    response = async_rest_api(URI, auth=token)
    print(response)


def test_matrix_01():
    URI = API_URL + '/matrix/organism?id=mgm4440281.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0'
    obj = obj_from_url(URI)
    o = open("1.txt", "w")
    o.write(str(obj))
    os.remove("1.txt")
def test_matrix_02():
    URI = API_URL + '/matrix/organism?id=mgm4440282.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0'
    obj = obj_from_url(URI)
    o = open("2.txt", "w")
    o.write(str(obj))
    os.remove("2.txt")

def test_matrix_03():
    URI = API_URL + '/matrix/organism?id=mgm4440283.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0'
    obj = obj_from_url(URI)
    o = open("3.txt", "w")
    o.write(str(obj))
    os.remove("3.txt")

def test_matrix_04():
    URI = API_URL + '/matrix/organism?id=mgm4440284.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0'
    obj = obj_from_url(URI)
    o = open("4.txt", "w")
    o.write(str(obj))

def test_large_01():
    URI = API_URL + '/matrix/organism?group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0&id=mgm4510219.3'
    obj = obj_from_url(URI)
    o = open("5.txt", "w")
    o.write(str(obj))
    os.remove("5.txt")

def test_large_02():
    URI = API_URL + '/matrix/organism?group_level=phylum&source=RefSeq&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0&id=mgm4510219.3'
    obj = obj_from_url(URI)
    o = open("6.txt", "w")
    o.write(str(obj))
    os.remove("6.txt")

def test_large_03():
    URI = API_URL + '/matrix/organism?group_level=phylum&source=SEED&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0&id=mgm4510219.3'
    obj = obj_from_url(URI)
    o = open("7.txt", "w")
    o.write(str(obj))
    os.remove("7.txt")
