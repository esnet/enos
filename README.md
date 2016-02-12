enos
====

The ESnet Network Operating System (ENOS) is a software system that provides a secure execution environment 
for network functions, as well as some that can be useful in building network control plane applications.
  
Quickstart
----------

This section documents a set of steps to install ENOS onto an existing host, with OpenDaylight and Corsa SDX3
integration.  It is possible, via a slightly different workflow, to get an ENOS deployment with a subset of this functionality,
should that not be needed or desired.  These instructions are believed to work for 
Linux (CentOS 7 with Oracle Java 7) and MacOS (Yosemite and El Capitan with Oracle Java 7).

A more comprehensive document, which covers installation of ENOS into a fresh virtual machine, can be found at:

https://docs.google.com/document/d/1_RzUkPTbHVtEnj_dBALiAvT9aHxL1ms6Pw6mdnaBM3c

Installation
------------

1.  The first step is to obtain a suitable Karaf container.  If using Corsa SDX3 integration, a
    customized install of Open Daylight (ODL) is available that contains both ODL and the SDX3 driver (as
    of this writing, a distribution based on ODL Lithium-SR1 has been successfully tested).
    Instructions on obtaining the driver distribution are beyond the scope of this document, but it will 
    be assumed that the Karaf container has been obtained and unpacked.

2.  Install Oracle Java 7, Maven, and rabbitmq-server.  

3.  Check out both the netshell and enos software repositories from Github:

        git clone https://github.com/esnet/netshell
        git clone https://github.com/esnet/enos
        
4.  From the top-level directory of the ODL Karaf distribution, execute the ```distribution/karaf/fixup-karaf.sh```
    script found in the top-level directory of the ```netshell``` source tree.
    This change restores the default search behavior for finding bundles in Maven
    repositories (in particular it's needed to read the NetShell bundles from the local Maven
    repository / cache).
    
5.  ODL does not play well with the ENOS security manager (the exact conditions
    are not completely known).  To work around this problem, the ENOS security manager must be disabled.
    Create a file named ```netshell.json``` in the top level directory of the Karaf, with these contents:
    
        {
            "global": {
        	    "securityManagerDisabled":	1
            }
        }

6.  Create the root directory where ENOS will store its state.  By default this is ```/var/netshell```.
    Also create some initialization files needed for ENOS's Python interpreter.
    
        mkdir /var/netshell
        chown $USER /var/netshell     # if needed
        mkdir /var/netshell/etc
        touch /var/netshell/etc/init.py
        cp netshell/distribution/netshell-root/etc/profile.py /var/netshell/etc/init.py/

7.  Compile and install the netshell and enos sources to the local Maven cache:

        (cd netshell && mvn install)
        (cd enos && mvn install)
        
8.  Start up the ODL Karaf container from the top-level directory of the ODL Karaf installation with ```bin/karaf```.

9.  Within the Karaf instance, load the ODL features of interest, such as OpenFlow support and the
    DLUX GUI:
    
        feature:install odl-dlux-all odl-openflowplugin-all
            
    It is possible (but not required) to test the ODL DLUX WebUI by going to the following URL:
    
        http://localhost:8181/index.html

10. Features necessary for NetShell integration can be loaded as follows:
    
        feature:install odl-openflowplugin-adsal-compatibility odl-nsf-managers

11. To make the embedded SSH server start up correctly, it is necessary to refresh the bindings of one
    of the bundles.

        bundle:refresh -f org.apache.sshd.core

    This is necessary so that the org.apache.sshd.core contains correct bindings for
    the org.apache.mina.service package.  These bindings are necessary for NetShell's embedded SSH
    server; failure to get this right results in a a runtime exception at NetShell startup time.

12. Execute the following command to make the NetShell feature repository available:

        feature:repo-add mvn:net.es/netshell-kernel/1.0-SNAPSHOT/xml/features

13. Execute the following commands as applicable to start NetShell for the first time:

        feature:install netshell-kernel
        feature:install netshell-python
        
    The feature installation of netshell-python may generate some exceptions and warnings, which
    can (probably) be ignored.
    
14. To load the NetShell OpenDaylight MD-SAL bundles:

        feature:install netshell-odl-mdsal netshell-odl-corsa-intf
        feature:install netshell-odl-corsa
        feature:install netshell-controller

15. Add the feature repository and install the feature:

        feature:repo-add mvn:net.es/enos-esnet/1.0-SNAPSHOT/xml/features

        feature:install enos-esnet

16. Optionally, execute the following commands (needed the first time only) to initialize the ESnet topology.
    Future runs will have this topology cached:

        python

        from net.es.enos.esnet import ESnetTopology
        ESnetTopology.registerToFactory()


Simulated ESnet 100G SDN testbed using Mininet
----------------------------------------------

(NOTE:  Instructions in this section have not been tested recently.)

ESnet 100G SDN testbed can be simulated within a virtual machine using Mininet:

1, Download the latest Mininet version from http://mininet.org/download/ 

2. Run and configure the Mininet VM making but do not run the walkthrough tutorial: it would create persistent virtual switches
   that would interfere with the overall simlation. 

3. From the ENOS ```esnet/src/main/python/mininet/``` directory, copy testbed.py and run.py into the mininet VM.
   Configure testbed.py to point to the IP/port address of OpendayLight. (this will be improved to use an option in the future)

4. On the mininet VM, run "sudo python run.py". This script will create the 8 SDN pops of the testbed, including ESnet core routers, 
   SDN physical switches, OVS and service VM.  Note that the topology is currently hard
   coded in the first lines of testbed.py.

Copyright
---------

ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
of the University of California, through Lawrence Berkeley National
Laboratory (subject to receipt of any required approvals from the
U.S. Dept. of Energy).  All rights reserved.

If you have questions about your rights to use or distribute this
software, please contact Berkeley Lab's Innovation & Partnerships
Office at IPO@lbl.gov.

NOTICE.  This Software was developed under funding from the
U.S. Department of Energy and the U.S. Government consequently retains
certain rights. As such, the U.S. Government has been granted for
itself and others acting on its behalf a paid-up, nonexclusive,
irrevocable, worldwide license in the Software to reproduce,
distribute copies to the public, prepare derivative works, and perform
publicly and display publicly, and to permit other to do so.

