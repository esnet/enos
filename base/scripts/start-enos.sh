#!/bin/sh

PYTHON_CACHEDIR=/tmp/cachedir
JAVA=java

$JAVA -Dpython.cachedir.skip=true -Dpython.cachedir=$PYTHON_CACHEDIR -jar $ENOS_HOME/target/enos-1.0-SNAPSHOT.one-jar.jar
