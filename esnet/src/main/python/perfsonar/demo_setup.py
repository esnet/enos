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

"""
demo should be run no more than once to initialize the topology and add the perfsonar testers
"""


from layer2.testbed.topology import TestbedTopology
from net.es.enos.esnet import ESnetTopology
from net.es.enos.esnet import PerfSONARTester


#identifying pt hosts should  be part of the general topology code and not just part of ps_demo
def add_ps_nodes():
    #it would be better to use the TopologyProvider.getInstance but that isn't working. Hence this tempoary code
    estopo = ESnetTopology()

    if (estopo):
        links = estopo.getLinks()
        for link in links:
            if "pt" in link:

                desc=ESnetTopology.idToDescription(link)
                
                ps_node= PerfSONARTester()

                node_name = desc[3:]
                ps_node.setResourceName(node_name)
                ps_node.addLink(links.get(link))
                perf_testers[node_name+'.es.net'] = ps_node

def main():
    if not 'topo' in globals() or topo == None:
        global topo
        topo=TestbedTopology()

    if not 'PSTests' in globals():
        PSTests = {}
        globals()['PSTests'] = PSTests

    if not 'perf_testers' in globals():
       global perf_testers
    
    perf_testers=dict()

    add_ps_nodes()


if __name__ == '__main__':
    main()
