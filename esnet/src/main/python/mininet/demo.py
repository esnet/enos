from mininet.sites import SiteIntent, SiteRenderer
from common.openflow import SimpleController
from mininet.enos import TestbedTopology

if __name__ == '__main__':
    # todo: real argument parsing.
    if not SiteRenderer.instance:
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
                serviceVm = site.props['serviceVm'].props['enosNode']
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
                    if srcNode in siteNodes and dstNode in siteNodes:
                        enosLinks.append(link)
                intent = SiteIntent(name=site.name,hosts=enosHosts,borderRouter=borderRouter,siteRouter=siteRouter,links=enosLinks)
                global renderer
                renderer = SiteRenderer(intent)
                err = renderer.execute()
    else:
        if SiteRenderer.lastEvent:
            SiteRenderer.instance.eventListener(SiteRenderer.lastEvent)




