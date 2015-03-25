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


Simulated ESnet 100G SDN testbed using Mininet
----------------------------------------------

ESnet 100G SDN testbed can be simulated within a virtual machine using Mininet:

1, Download the latest Mininet version  //http://mininet.org/download/. 

2. Run and configure the Mininet VM making but do not run the walkthrough tutorial: it would create persistent virtual switches
   that would interfere with the overall simlation. 

3. From the ENOS python src directory, copy testbed.py and run.py into the mininet VM.
   Configure testbed.py to point to the IP/port address of OpendayLight. (this will be improved to use an option in the future)

4. On the mininet VM, run "sudo python run.py". This script will create the 8 SDN pops of the testbed, including ESnet core routers, 
   SDN physical switches, OVS and service VM. It will also create a VPN instance that. Note that the topology is currently hard
   coded in the first lines of testbed.py

