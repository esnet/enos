#/bin/python
#
# Configures the initial ENOS deployment. Currently hard coded for ESnet deployment
#
from net.es.enos.configuration import GlobalConfiguration;

print "Welcome to ENOS configuration tool."
print "\t.currently only support ESnet deployment"
print '\t.add " around strings (python type)'
print


enosroot = input("ENOS Root directory: ")

#Try to instantiate a configuration
config = GlobalConfiguration.getInstance()
config.canSet()