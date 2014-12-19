#!/bin/sh
JAVA=java

if [ "x$ENOS_CONF" = "x" ]; then
    export ENOS_CONF=./enos.json
fi
echo "Setting ENOS_CONF to $ENOS_CONF"
if [ "x$ENOS_HOME" = "x" ]; then
    export ENOS_HOME=/tmp/enos
fi
echo "Setting ENOS_HOME to $ENOS_HOME"

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
export ENOS_DISTRO=$SCRIPT_DIR/..

# make sure directory exist and create default ACL
mkdir -p  $ENOS_HOME/bin
mkdir -p  $ENOS_HOME/.acl
echo "read=all" > $ENOS_HOME/.acl/bin

# copy python code into /bin
find $ENOS_DISTRO/src -name "*.py" -exec cp {} $ENOS_HOME/bin \;
