from mininet.sites import SiteIntent, SiteRenderer
from common.openflow import SimpleController
from mininet.enos import TestbedTopology
from mininet.l2vpn import SDNPopsRenderer,SDNPopsIntent
from net.es.netshell.api import GenericGraphViewer

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
    enosHosts = []
    sdnHosts = []
    pops = []
    for (x,vpn) in net.builder.vpns.items():
        sites = vpn.props['sites']
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
            pops.append((borderRouter,serviceVm))
            siteNodes.append(siteRouter)
            siteNodes.append(borderRouter)
            links = site.props['links'].copy()
            enosLinks=[]
            popsLinks = []
            for (z,l) in links.items():
                link = l.props['enosLink']
                node1 = link.getSrcNode()
                node2 = link.getDstNode()
                srcNode = link.getSrcNode()
                dstNode = link.getDstNode()
                if srcNode in siteNodes and dstNode in siteNodes:
                    enosLinks.append(link)
                    continue
                if srcNode in [borderRouter,hwSwitch] and dstNode in [borderRouter,hwSwitch]:
                    popsLinks.append(link)
                if srcNode in [swSwitch,hwSwitch] and dstNode in [swSwitch,hwSwitch]:
                    popsLinks.append(link)
                if srcNode in [swSwitch,serviceVm] and dstNode in [swSwitch,serviceVm]:
                    popsLinks.append(link)

            intent = SiteIntent(name=site.name,hosts=enosHosts,borderRouter=borderRouter,siteRouter=siteRouter,links=enosLinks)
            global renderer
            renderer = SiteRenderer(intent)
            err = renderer.execute()
            #viewer = GenericGraphViewer(intent.buildGraph())
            #viewer.display()
            print "SDN intent"
            popsIntent = SDNPopsIntent(name=vpn.name,pops=pops,hosts=sdnHosts,links=popsLinks)
            popsRenderer = SDNPopsRenderer(popsIntent)
            popsRenderer.execute()







