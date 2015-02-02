#! /bin/sh

LIB=tools/lib
LOCAL=`pwd`

# adding lib to python and perl env
LIB_PATH=$LOCAL/$LIB
export PYTHONPATH=$PYTHONPATH:$LIB_PATH
export PERL5LIB=$PERL5LIB:$LIB_PATH
