#/bin/python
#
# Configures the initial ENOS deployment. Currently hard coded for ESnet deployment
#
from net.es.enos.esnet import ESnetTopology, ESnet, DataTransferNode, DataTransferNodeInterface
from java.lang import Integer

# Creates ESnet DataTransferNode's
def createDTN(name, type, interfaces):
   dtn = DataTransferNode()
   dtn.setName(name)
   dtn.setType(type)
   for interface in interfaces:
       i = DataTransferNodeInterface()
       i.setName(interface[0])
       i.setSpeed(interface[1])
       for vlan in interface[2]:
           i.getVlans().add(Integer(vlan))
       for link in interface[3]:
           i.getLinks().add(link)
       dtn.getInterfaces().add(i)
   dtn.save()





# Register ESnetTopology as the defaul local layer2 topology provider
ESnetTopology.registerToFactory()

# Register ESnet as the defaul local layer2 network provider
ESnet.registerToFactory()

createDTN(name="bnl-diskpt1",type=10000000000,
          interfaces = [
              ["eth2",10000000000,[3609,834,3179,343,916],
               ["eth2",10000000000,"urn:ogf:network:es.net:bnl-mr3:xe-7/0/0"]]
          ])

createDTN(name="lbl-diskpt1",type=10000000000,
          interfaces = [
              ["eth2",10000000000,[1300,3609,246,202,916],
               ["eth2",10000000000,"urn:ogf:network:es.net:lbl-mr2:xe-9/3/0"]]
          ])

createDTN(name="anl-diskpt1",type=10000000000,
          interfaces = [
              ["eth2",10000000000,[1300,3609,246,202,916],
               ["eth2",10000000000,"urn:ogf:network:es.net:anl-mr2:xe-1/2/0]"]]
          ])

