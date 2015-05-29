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

intents = {}
renderers = {}

if __name__ == '__main__':
    configFileName = None
    net=None
    intent=None
    if len(sys.argv) > 1:
        configFileName = sys.argv[1]
        net = TestbedTopology(fileName=configFileName)
    else:
        net = TestbedTopology()

    # One-time setup for the VPN service
    wi = WanIntent("esnet", net.builder.pops.values())
    wr = WanRenderer(wi)
    wr.execute()

    for (x,vpn) in net.builder.vpns.items():
        enosHosts = []  # All hosts in this VPN
        sdnHosts = []   # All nodes in this VPN (end hosts, routers, service VMs)
        sites = vpn.props['sites']
        popsLinks = []
        pops = []
        for (y,site) in sites.items():
            hosts = site.props['hosts']
            siteHosts=[]    # Hosts on this site
            siteNodes=[]    # Nodes on this site (end hosts, routers, service VMs)
            for(z,h) in hosts.items():
                host = h.props['enosNode']
                enosHosts.append(host)
                siteHosts.append(host)
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
            for (z,l) in links.items():
                link = l.props['enosLink']
                node1 = link.getSrcNode()
                node2 = link.getDstNode()
                srcNode = link.getSrcNode()
                dstNode = link.getDstNode()
                if borderRouter.name in [srcNode.getResourceName(),dstNode.getResourceName()]:
                    pop.props['vpnVlan'] = link.props['vlan']
                if srcNode in siteNodes and dstNode in siteNodes:
                    enosLinks.append(link)
                    continue
            print "Creates SiteIntent for vpn " + vpn.name + " site " + site.name
            intent = SiteIntent(name=site.name,hosts=siteHosts,borderRouter=borderRouter,siteRouter=siteRouter,links=enosLinks)
            global renderer
            renderer = SiteRenderer(intent)
            err = renderer.execute()
            #viewer = GenericGraphViewer(intent.buildGraph())
            #viewer.display()

        popsLinks = []

        for srcPop in pops:
            for dstPop in pops:
                if srcPop == dstPop:
                    continue
                link = net.builder.pops[srcPop.name].props['hwSwitch'].props['nextHop'][dstPop.name]
                link.props['enosLink'].props['vpnVlans'] = [link.props['vlan']]
                popsLinks.append(link.props['enosLink'])
            links = srcPop.props['hwSwitch'].props['toCoreRouter']
            vpnVlan = srcPop.props['vpnVlan']
            for link in links:
                # Strip suffix, get endpoints
                eps = "-".join(link.name.split("-")[0:-1]).split(':')
                enosLink = link.props['enosLink']
                if not 'vpnVlans' in enosLink.props:
                    enosLink.props['vpnVlans'] = []
                if not "vlan" in link.name and not vpnVlan in enosLink.props['vpnVlans']:
                    enosLink.props['vpnVlans'] = [vpnVlan]
                    popsLinks.append(enosLink)

        popsIntent = SDNPopsIntent(name=vpn.name,pops=pops,hosts=sdnHosts,links=popsLinks)
        popsRenderer = SDNPopsRenderer(popsIntent)
        popsRenderer.execute()
        print "VPN " + vpn.name + " is up."
        #viewer = GenericGraphViewer(popsIntent.graph)
        #viewer.display()







