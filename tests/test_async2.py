#!/usr/bin/env python

from mglib import get_auth_token, async_rest_api, API_URL

def test_async():
    URI = API_URL + '/matrix/organism?hit_type=single&group_level=strain&evalue=15&source=RefSeq&result_type=abundance&id=mgm4653783.3&asynchronous=1'
    token = get_auth_token(None)
    print("MG-RAST token: ", token)
    response = async_rest_api(URI, auth=token)
    print(repr(response))
#    print("writing test_async.txt")
#    o=open("test_async.txt", "w")
#    o.write(response)
if __name__ == '__main__':
    test_async()
