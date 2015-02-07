enos
====

ESnet Network Operating System

Installation
------------

Into a Karaf container where there's already a working netshell-kernel and netshell-python:

1.  Add the feature repository and install the feature:

        feature:repo-add mvn:net.es/enos-esnet/1.0-SNAPSHOT/xml/features

        feature:install enos-esnet

2.  Execute the following commands (needed the first time only) to initialize the ESnet topology.
    Future runs will have this topology cached:

        python

        from net.es.enos.esnet import ESnetTopology
        ESnetTopology.registerToFactory()

