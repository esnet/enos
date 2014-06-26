#/bin/python
#
# Configures the initial ENOS deployment. Currently hard coded for ESnet deployment
#
from net.es.enos.esnet import ESnetTopology

print "Welcome to ENOS configuration tool."
print "\t.currently only support ESnet deployment"
print '\t.add " around strings (python type) when entering strings'
print

print "registering ESnet Topology as default layer 2 topology service"
ESnetTopology.registerToFactory()

