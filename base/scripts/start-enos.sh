#!/bin/sh
#
# This scripts assumes that the shell variable ENOS_ROOTDIR is set to the directory with write access where all
# the ENOS files will be located.
#
JAVA=java
if [ "x$ENOS_ROOTDIR" = "x" ]; then
    export ENOS_ROOTDIR=/tmp/enos
    echo "Setting ENOS_ROOTDIR to $ENOS_ROOTDIR"
fi
if [ "x$ENOS_HOME" = "x" ]; then
    export ENOS_HOME=$PWD
    echo "Setting ENOS_HOME to $ENOS_HOME"
fi

SYSTEM_PROPS="-Denos.rootdir=${ENOS_ROOTDIR} -Dorg.slf4j.simpleLogger.showDateTime=true"

$JAVA $SYSTEM_PROPS -jar $ENOS_HOME/target/enos-1.0-SNAPSHOT.one-jar.jar
