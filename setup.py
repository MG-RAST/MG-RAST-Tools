#!/usr/bin/env python

import sys, glob

from setuptools import setup

setup(name='mglib',
    version='1.1',
    description='MG-RAST Tools',
    author='The MG-RAST team',
    author_email='help@mg-rast.org',
    url='https://github.com/MG-RAST/MG-RAST-Tools',
    packages=['mglib'],
    scripts=glob.glob('scripts/[a-z]*') + glob.glob('examples/python/*.py'),
    install_requires=  ['prettytable >= 0.7', 
                        'requests_toolbelt >= 0.8', 
                        'setuptools > 29.0' ]  # >28 fail
     )


