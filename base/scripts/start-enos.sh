#!/bin/sh
#
# This scripts assumes that the shell variable ENOS_ROOTDIR is set to the directory with write access where all
# the ENOS files will be located.
#
JAVA=java
if [ "x$ENOS_ROOTDIR" = "x" ]; then
    export ENOS_ROOTDIR=/tmp/enos
fi
echo "Setting ENOS_ROOTDIR to $ENOS_ROOTDIR"
if [ "x$ENOS_HOME" = "x" ]; then
    export ENOS_HOME=$PWD
fi
echo "Setting ENOS_HOME to $ENOS_HOME"
if [ "x$ENOS_LOGLEVEL" = "x" ]; then
    export xENOS_LOGLEVEL=info
fi
echo "Setting ENOS_LOGLEVEL to $ENOS_LOGLEVEL"
if [ "x$ENOS_SECURITYMANAGER" = "x" ]; then
    export xENOS_SECURITYMANAGER=yes
fi
echo "Setting ENOS_SECURITYMANAGER to $ENOS_SECURITYMANAGER"
SYSTEM_PROPS="-Denos.securitymanager=${ENOS_SECURITYMANAGER} -Dorg.slf4j.simpleLogger.defaultLogLevel=${ENOS_LOGLEVEL} -Denos.rootdir=${ENOS_ROOTDIR} -Dorg.slf4j.simpleLogger.showDateTime=true"

$JAVA $SYSTEM_PROPS -jar $ENOS_HOME/target/enos-1.0-SNAPSHOT.one-jar.jar
