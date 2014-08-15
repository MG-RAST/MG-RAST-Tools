#! /bin/sh

LIB=tools/lib
LOCAL=`pwd`

# adding lib to PYTHONPATH 
PYTHONPATH=$PYTHONPATH:$LOCAL/$LIB
export $PYTHONPATH