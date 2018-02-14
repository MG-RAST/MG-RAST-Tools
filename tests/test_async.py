#!/usr/bin/env python

from mglib.mglib import get_auth_token, async_rest_api, API_URL

def test_async0():
    URI = API_URL + '/matrix/organism?id=mgm4440275.3&id=mgm4440276.3&id=mgm4440281.3&group_level=phylum&source=RDP&hit_type=single&result_type=abundance&evalue=1&identity=60&length=15&taxid=0&asynchronous=1'
    token = get_auth_token(None)
    print(token)
    response = async_rest_api(URI, auth=token)
    print(repr(response))

if __name__ == "__main__":
    test_async0()
