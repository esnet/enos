#!/bin/sh
#
# This scripts assumes that the shell variable ENOS_ROOTDIR is set to the directory with write access where all
# the ENOS files will be located.
#
JAVA=java
SYSTEM_PROPS="-Denos.rootdir=$ENOS_ROOTDIR"
SYSTEM_PROPOS=$SYSTEM_PROPS +  "/jyphon-cachedir"

$JAVA $SYSTEM_PROPS -jar $ENOS_HOME/target/enos-1.0-SNAPSHOT.one-jar.jar
