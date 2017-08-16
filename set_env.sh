#! /bin/sh

LIB=tools/lib
LOCAL=`pwd`

# missing check for Ubuntu 14.04
# ./PATH/set_env.sh not setting path correctly on Ubuntu

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $DIR



# adding lib to python and perl env
LIB_PATH=$DIR/$LIB
echo PYTHONPATH = $LIB_PATH
export PYTHONPATH=$PYTHONPATH:$LIB_PATH
export PERL5LIB=$PERL5LIB:$LIB_PATH
export KB_PERL_PATH=$LIB_PATH