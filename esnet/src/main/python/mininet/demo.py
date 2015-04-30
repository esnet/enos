from mininet.sites import SiteIntent, SiteRenderer
from common.openflow import SimpleController
from mininet.enos import TestbedTopology
from mininet.l2vpn import SDNPopsRenderer,SDNPopsIntent
from mininet.wan import WanRenderer, WanIntent
from net.es.netshell.api import GenericGraphViewer

import copy

def getPop(topo,coreRouter):
    pops = topo.builder.pops
    for (x,pop) in pops.items():
        if pop.props['coreRouter'].name == coreRouter.name:
            return pop
    return None

if __name__ == '__main__':
    configFileName = None
    net=None
    intent=None
    if len(sys.argv) > 1:
        configFileName = sys.argv[1]
        net = TestbedTopology(fileName=configFileName)
    else:
        net = TestbedTopology()

    # clean up the Controller's scope
    SimpleController.scopes = {}

    # One-time setup for the VPN service
    wi = WanIntent("esnet", net.builder.pops.values())
    wr = WanRenderer(wi)
    wr.execute()

    enosHosts = []
    sdnHosts = []
    pops = []

    for (x,vpn) in net.builder.vpns.items():
        enosHosts = []
        sdnHosts = []
        sites = vpn.props['sites']
        popsLinks = []
        pops = []
        for (y,site) in sites.items():
            hosts = site.props['hosts']
            siteNodes=[]
            for(z,h) in hosts.items():
                host = h.props['enosNode']
                enosHosts.append(host)
                siteNodes.append(host)
            siteRouter = site.props['siteRouter'].props['enosNode']
            borderRouter = net.nodes[site.props['connectedTo']]
            pop = getPop(topo=net,coreRouter=borderRouter)
            pops.append(pop)
            hwSwitch = pop.props['hwSwitch']
            swSwitch = pop.props['swSwitch']
            serviceVm = site.props['serviceVm'].props['enosNode']
            sdnHosts.append(borderRouter)
            sdnHosts.append(hwSwitch)
            sdnHosts.append(swSwitch)
            sdnHosts.append(serviceVm)
            siteNodes.append(siteRouter)
            siteNodes.append(borderRouter)
            links = site.props['links'].copy()
            enosLinks=[]
            vpnVlan = None
            for (z,l) in links.items():
                link = l.props['enosLink']
                node1 = link.getSrcNode()
                node2 = link.getDstNode()
                srcNode = link.getSrcNode()
                dstNode = link.getDstNode()
                if borderRouter.name in [srcNode.getResourceName(),dstNode.getResourceName()]:
                    vpnVlan = link.props['vlan']
                if srcNode in siteNodes and dstNode in siteNodes:
                    enosLinks.append(link)
                    continue
            print "Creates SiteIntent for vpn " + vpn.name + " site " + site.name
            intent = SiteIntent(name=site.name,hosts=enosHosts,borderRouter=borderRouter,siteRouter=siteRouter,links=enosLinks)
            global renderer
            renderer = SiteRenderer(intent)
            err = renderer.execute()
            #viewer = GenericGraphViewer(intent.buildGraph())
            #viewer.display()
            links = hwSwitch.props['toCoreRouter']
            for link in links:
                # Strip suffix, get endpoints
                eps = "-".join(link.name.split("-")[0:-1]).split(':')
                if hwSwitch.name in eps and borderRouter.name in eps:
                    enosLink = link.props['enosLink']
                    if not 'vpnVlans' in enosLink.props:
                        enosLink.props['vpnVlans'] = []
                    #print "SITE",site.name,"LINK",link.name,"VLANS",enosLink.props['vpnVlans']
                    if "vlan" in link.name:
                        enosLink.props['vpnVlans'].append(enosLink.props['vlan'])
                    else:
                        enosLink.props['vpnVlans'].append(vpnVlan)
                    popsLinks.append(enosLink)

        # prunes links to pop's that are not in pops
        for link in popsLinks:
            print link
        print "Creates SDNPopsIntent for vpn " + vpn.name, "\nPOPS\n",pops, "\nHOSTS\n",sdnHosts
        popsIntent = SDNPopsIntent(name=vpn.name,pops=pops,hosts=sdnHosts,links=popsLinks)
        popsRenderer = SDNPopsRenderer(popsIntent)
        popsRenderer.execute()
        print "VPN " + vpn.name + " is up."
        #viewer = GenericGraphViewer(popsIntent.graph)
        #viewer.display()







