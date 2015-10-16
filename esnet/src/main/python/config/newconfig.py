#/bin/python
#
# ENOS, Copyright (c) 2015, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov.
#
# NOTICE.  This software is owned by the U.S. Department of Energy.  As such,
# the U.S. Government has been granted for itself and others acting on its
# behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software
# to reproduce, prepare derivative works, and perform publicly and display
# publicly.  Beginning five (5) years after the date permission to assert
# copyright is obtained from the U.S. Department of Energy, and subject to
# any subsequent five (5) year renewals, the U.S. Government is granted for
# itself and others acting on its behalf a paid-up, nonexclusive, irrevocable,
# worldwide license in the Software to reproduce, prepare derivative works,
# distribute copies to the public, perform publicly and display publicly, and
# to permit others to do so.
#
#
# Configures the initial ENOS deployment. Currently hard coded for ESnet deployment
#
from net.es.enos.esnet import ESnetTopology, ESnet, DataTransferNode, DataTransferNodeInterface, DataTransferNodeLink
from java.util import ArrayList

# Creates ESnet DataTransferNode's
def createDTN(name, type, interfaces, links):
   dtn = DataTransferNode()
   dtn.setName(name)
   dtn.setType(type)
   dtn.setInterfaces(ArrayList())
   for interface in interfaces:
       i = DataTransferNodeInterface()
       i.setIfName(interface[0])
       i.setSpeed(interface[1])
       i.setIfLinks(ArrayList())
       i.setVlans(ArrayList())
       for vlan in interface[2]:
           i.getVlans().add(vlan)
       link = DataTransferNodeLink()
       link.setHostPort(links[0])
       link.setCapacity(links[1])
       link.setRemoteId(links[2])
       i.getIfLinks().add(link)
       dtn.getInterfaces().add(i)
   dtn.save()





# Register ESnetTopology as the defaul local layer2 topology provider
ESnetTopology.registerToFactory()

# Register ESnet as the defaul local layer2 network provider
ESnet.registerToFactory()

createDTN(name="bnl-diskpt1",type="10000000000",
          interfaces =
              [["eth2","10000000000",["3609","834","3179","343","916"]]],
          links = ["eth2","10000000000","urn:ogf:network:es.net:bnl-mr3:xe-7/3/0"],
          )

createDTN(name="lbl-diskpt1",type="10000000000",
          interfaces =
              [["eth2","10000000000",["1300","3609","246","202","916"]]],
          links = ["eth2","10000000000","urn:ogf:network:es.net:lbl-mr2:xe-9/3/0"],
          )

createDTN(name="anl-diskpt1",type="10000000000",
          interfaces =
              [["eth2","10000000000",["1300","3609","246","202","916"]]],
          links = ["eth2","10000000000","urn:ogf:network:es.net:anl-mr2:xe-1/2/0"],
          )

