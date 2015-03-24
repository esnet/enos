from net.es.enos.perfsonar import SimpleLookupService
from net.es.lookup.queries.Network import PSMetadataQuery

# Query sls to get stuff

# Instantiate sLS client
sls = SimpleLookupService()

# Retrieve all hosts in es.net domain
hosts = sls.retrieveHostsByDomain("es.net")

print "=== hosts ==="
for h in hosts:
    print h.getId()
    for i in h.getInterfaces():
        print "   ", i.getIfName(), i.getAddresses()

# Try to get psmetadata records
q = PSMetadataQuery()
psms = sls.queryPSMetadata(q)
print "=== psmetadata URIs ==="
for psm in psms:
    print psm.getPsmUri()

