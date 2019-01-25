#!/usr/bin/env python
def test_dependencies():
    try:
        import numpy
    except ImportError:
        print("numpy not found.  ")

    try:
        import requests
    except ImportError:
        print("requests not found. ")
    try:
        import scipy
    except ImportError:
        print("scipy not found.  ")
    try:
        import requests_toolbelt
    except ImportError:
        print("requests_toolbelt not found.  ")
