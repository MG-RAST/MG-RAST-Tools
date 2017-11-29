#!/usr/bin/env python

import mglib
import urllib
from mglib.mglib import get_auth_token, async_rest_api

APIURL = "http://api.metagenomics.anl.gov/"

def test_async():
    URI = APIURL + 'matrix/organism?id=mgm4440275.3&id=mgm4440276.3&id=mgm4440281.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0'
    URI = APIURL + 'matrix/organism?id=mgm4440275.3&id=mgm4440276.3&id=mgm4440281.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0&asynchronous=1'
    token = get_auth_token(None)
    print(token)
    response = async_rest_api(URI, auth=token)
    print(type(response))

test_async()
