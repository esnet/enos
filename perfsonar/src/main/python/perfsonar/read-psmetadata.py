#
# ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
# of the University of California, through Lawrence Berkeley National
# Laboratory (subject to receipt of any required approvals from the
# U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this
# software, please contact Berkeley Lab's Innovation & Partnerships
# Office at IPO@lbl.gov.
#
# NOTICE.  This Software was developed under funding from the
# U.S. Department of Energy and the U.S. Government consequently retains
# certain rights. As such, the U.S. Government has been granted for
# itself and others acting on its behalf a paid-up, nonexclusive,
# irrevocable, worldwide license in the Software to reproduce,
# distribute copies to the public, prepare derivative works, and perform
# publicly and display publicly, and to permit other to do so.
#
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

