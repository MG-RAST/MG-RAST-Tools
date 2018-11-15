FROM ubuntu:16.04

RUN apt-get update && apt-get install -y git make python python-setuptools  gcc  python-dev python-pytest 

# setproctile  needs Python.h from python-dev
# requests needs gcc to build
RUN git clone http://github.com/wltrimbl/MG-RAST-Tools
RUN cd MG-RAST-Tools && make install  
