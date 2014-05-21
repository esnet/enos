#!/bin/sh
JAVA=java

if [ "x$ENOS_CONF" = "x" ]; then
    export ENOS_CONF=./enos.json
fi
echo "Setting ENOS_CONF to $ENOS_CONF"
if [ "x$ENOS_HOME" = "x" ]; then
    export ENOS_HOME=$PWD
fi
echo "Setting ENOS_HOME to $ENOS_HOME"
if [ "x$ENOS_LOGLEVEL" = "x" ]; then
    export ENOS_LOGLEVEL=info
fi
echo "Setting ENOS_LOGLEVEL to $ENOS_LOGLEVEL"

SYSTEM_PROPS="-Denos.configuration=${ENOS_CONF} -Dorg.slf4j.simpleLogger.defaultLogLevel=${ENOS_LOGLEVEL} -Denos.rootdir=${ENOS_ROOTDIR} -Dorg.slf4j.simpleLogger.showDateTime=true"

$JAVA $SYSTEM_PROPS -jar $ENOS_HOME/target/enos-1.0-SNAPSHOT.one-jar.jar
