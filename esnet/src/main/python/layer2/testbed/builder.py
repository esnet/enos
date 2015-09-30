#!/usr/bin/python

import struct,binascii
from array import array

from layer2.common.api import Node, SDNPop, Link, Port, Site, Wan, VPN, Host, HwSwitch, SwSwitch, Switch
from layer2.common.mac import MACAddress
from layer2.testbed import dpid, oscars

# All switches including site routers, core routers, hw switches, and sw switches should
# not have the same name so that the name of each port could be unique.
# site = [siteRouterName, [hostNames], popName, portNo]
# Note: Since flowmod could not forward a packet to where it comes from,
#  multiple sites in the same pop must have different portNo! (otherwise, the broadcast won't work.)

# Simulated sites ESnet production diskpt's
lblsite = ["lbl.gov",['lbl-diskpt1'],"denv"]
anlsite = ["anl.gov",['anl-diskpt1'],"wash"]
bnlsite = ["bnl.gov",['bnl-diskpt1'],"aofa"]

sites = [lblsite, anlsite, bnlsite]

# DENV
denvlinks=[
    ["denv-cr5","9/1/4","denv-tb-of-1","23",'core'],
    ["denv-cr5","9/1/5","denv-tb-of-1","24",'site'],
    ["denv-ovs","eth10","denv-tb-of-1","1",'hw'],
    ["denv-ovs","eth11","denv-tb-of-1","2",'none']
]
denv=["denv",'denv-tb-of-1',"denv-cr5",denvlinks]


# WASH
washlinks = [
    ["wash-cr5","10/1/11","wash-tb-of-1","23",'core'],
    ["wash-cr5","10/1/12","wash-tb-of-1","24",'site'],
    ["wash-ovs","eth10","wash-tb-of-1","1",'hw'],
    ["wash-ovs","eth11","wash-tb-of-1","2",'none']
]
wash=["wash",'wash-tb-of-1',"wash-cr5", washlinks]

# AOFA
aofalinks = [
    ["aofa-cr5","10/1/3","aofa-tb-of-1","23",'core'],
    ["aofa-cr5","10/1/4","aofa-tb-of-1","24",'site'],
    ["aofa-ovs","eth10","aofa-tb-of-1","1",'hw'],
    ["aofa-ovs","eth11","aofa-tb-of-1","2",'none']
]
aofa=["aofa",'aofa-tb-of-1',"aofa-cr5",aofalinks]

# AMST
amstlinks = [
    ["amst-cr5","10/1/3","amst-tb-of-1","17",'core'],
    ["amst-cr5","10/1/4","amst-tb-of-1","18",'site'],
    ["amst-cr5","10/1/5","amst-tb-of-1","19",'none'],
    ["amst-cr5","10/1/6","amst-tb-of-1","20",'none'],
    ["amst-cr5","10/2/1","amst-tb-of-1","21",'none'],
    ["amst-cr5","10/2/2","amst-tb-of-1","22",'none'],
    ["amst-cr5","10/2/3","amst-tb-of-1","23",'none'],
    ["amst-cr5","10/2/4","amst-tb-of-1","24",'none'],
    ["amst-ovs","eth10","amst-tb-of-1","1",'hw'],
    ["amst-ovs","eth11","amst-tb-of-1","2",'none'],
    ["amst-ovs","eth12","amst-tb-of-1","3",'none'],
    ["amst-ovs","eth13","amst-tb-of-1","4",'none'],
    ["amst-ovs","eth14","amst-tb-of-1","5",'none'],
    ["amst-ovs","eth15","amst-tb-of-1","6",'none'],
    ["amst-ovs","eth16","amst-tb-of-1","7",'none'],
    ["amst-ovs","eth17","amst-tb-of-1","8",'none']
]
amst=["amst",'amst-tb-of-1',"amst-cr5",amstlinks]

# CERN
cernlinks = [
    ["cern-cr5","10/1/4","cern-tb-of-1","20",'core'],
    ["cern-cr5","10/1/5","cern-tb-of-1","21",'site'],
    ["cern-cr5","10/1/6","cern-tb-of-1","22",'none'],
    ["cern-cr5","10/2/5","cern-tb-of-1","23",'none'],
    ["cern-cr5","10/2/6","cern-tb-of-1","24",'none'],
    ["cern-ovs","eth10","cern-tb-of-1","1",'hw'],
    ["cern-ovs","eth11","cern-tb-of-1","2",'none'],
    ["cern-ovs","eth12","cern-tb-of-1","3",'none'],
    ["cern-ovs","eth13","cern-tb-of-1","4",'none'],
    ["cern-ovs","eth14","cern-tb-of-1","5",'none']
]
cern=["cern",'cern-tb-of-1',"cern-cr5",cernlinks]

# ATLA
atlalinks = [
    ["atla-cr5","10/1/9","atla-tb-of-1","21",'core'],
    ["atla-cr5","10/1/10","atla-tb-of-1","22",'site'],
    ["atla-cr5","10/1/10","atla-tb-of-1","23",'none'],
    ["atla-cr5","10/1/11","atla-tb-of-1","24",'none'],
    ["atla-ovs","eth10","atla-tb-of-1","1",'hw'],
    ["atla-ovs","eth11","atla-tb-of-1","2",'none'],
    ["atla-ovs","eth12","atla-tb-of-1","3",'none'],
    ["atla-ovs","eth13","atla-tb-of-1","4",'none']
]
atla=["atla",'atla-tb-of-1',"atla-cr5",atlalinks]

# STAR
starlinks = [
    ["star-cr5","9/2/3","star-tb-of-1","17",'core'],
    ["star-cr5","9/2/4","star-tb-of-1","18",'site'],
    ["star-cr5","9/2/5","star-tb-of-1","19",'none'],
    ["star-cr5","9/2/6","star-tb-of-1","20",'none'],
    ["star-cr5","10/1/5","star-tb-of-1","21",'none'],
    ["star-cr5","10/1/6","star-tb-of-1","22",'none'],
    ["star-cr5","10/1/11","star-tb-of-1","23",'none'],
    ["star-cr5","10/1/12","star-tb-of-1","24",'none'],
    ["star-ovs","eth10","star-tb-of-1","1",'hw'],
    ["star-ovs","eth11","star-tb-of-1","2",'none'],
    ["star-ovs","eth12","star-tb-of-1","3",'none'],
    ["star-ovs","eth13","star-tb-of-1","4",'none'],
    ["star-ovs","eth14","star-tb-of-1","5",'none'],
    ["star-ovs","eth15","star-tb-of-1","6",'none'],
    ["star-ovs","eth16","star-tb-of-1","7",'none'],
    ["star-ovs","eth17","star-tb-of-1","8",'none']
]
star=["star",'star-tb-of-1',"star-cr5",starlinks]

# LBL  POP is not yet deployed

# CORE TO CORE OSCARS circuits
#  GRI,src,dest,vlan. By convention, the source is always the router connected to the  host and the destination is
#  always the core router connected to the SDN POP.
corecircuits = [
    ['es.net-5909',
     'urn:ogf:network:domain=es.net:node=denv-cr5:port=9/1/4:link=*',
     'urn:ogf:network:domain=es.net:node=aofa-cr5:port=10/1/3:link=*',
     582] ,
    ['es.net-5906',
     'urn:ogf:network:domain=es.net:node=wash-cr5:port=10/1/11:link=*',
     'urn:ogf:network:domain=es.net:node=denv-cr5:port=9/1/4:link=*',
     3291],
    ['es.net-5908',
     'urn:ogf:network:domain=es.net:node=wash-cr5:port=10/1/11:link=*',
     'urn:ogf:network:domain=es.net:node=aofa-cr5:port=10/1/3:link=*',
     830]
]

# SITE to SDN POP OSCARS circuits
#  Site,GRI,src,dest,vlan
sitecircuits = {}

sitecircuits['lbl.gov'] = \
    ['lbl.gov',
     'es.net-5924',
     'urn:ogf:network:domain=es.net:node=lbl-mr2:port=xe-9/3/0:link=*',
     'urn:ogf:network:domain=es.net:node=denv-cr5:port=9/1/5:link=*',
     1994]

sitecircuits['anl.gov'] = \
    ['anl.gov',
     'es.net-5923',
     'urn:ogf:network:domain=es.net:node=anl-mr2:port=xe-1/2/0:link=*',
     'urn:ogf:network:domain=es.net:node=wash-cr5:port=10/1/12:link=*',
     2340]

sitecircuits['bnl.gov'] = \
    ['bnl.gov',
     'es.net-5925',
     'urn:ogf:network:domain=es.net:node=bnl-mr2:port=xe-2/2/0:link=*',
     'urn:ogf:network:domain=es.net:node=aofa-cr5:port=10/1/4:link=*',
     116]


# SDN POP's
locations=[denv,wash,aofa,amst,cern,atla,star]

class TopoBuilder ():

    debug = False;

    def __init__(self, fileName = None, controller = None):
        """
        Create a testbed topology
        :param fileName: filename for configuration (None for hard-coded default)
        :param network: Hash of ip, netmask for host IPv4 address assignment
        :param controller: Controller object (or subclass thereof)
        :return:
        """
        self.hostID = 1
        self.switchID = 1
        self.dpidIndex = 1
        self.hostIndex = {} # [hostname] = Host
        self.switchIndex = {} # [switchname] = Switch
        self.linkIndex = {} # [linkname] = Link
        self.siteIndex = {} # [sitename] = Site
        self.sitesConfig = []
        self.popIndex = {} # [popname] = SDNPop
        self.wan = Wan(name='esnet',topo=self)
        self.controller = controller

        if fileName != None:
            self.loadConfiguration(fileName)
        else:
            self.locations = locations
            self.sitesConfig = sites
        self.loadDefault()

    def addSwitch(self, switch):
        self.switchIndex[switch.name] = switch

    def addHost(self, host):
        self.hostIndex[host.name] = host

    def addLink(self, link):
        self.linkIndex[link.name] = link
        # Links are uni-directional. Create reverse link
        rl = Link(ports=[link.props['endpoints'][1],link.props['endpoints'][0]],
                  props=link.props,
                  vlan=link.props['vlan'])
        link.props['reverseLink'] = rl
        rl.props['reverseLink'] = link
        self.linkIndex[rl.name] = rl

    def addLinks(self, links):
        for link in links:
            self.addLink(link)

    def addSite(self,site):
        self.siteIndex[site.name] = site

    def addSDNPop(self, popname, hwswitchname, coreroutername, swswitchname,links):
        pop = SDNPop(name=popname,
                     hwswitchname=hwswitchname,
                     coreroutername=coreroutername,
                     swswitchname=swswitchname,
                     links=links)

        hwSwitch = pop.props['hwSwitch']
        swSwitch = pop.props['swSwitch']
        coreRouter = pop.props['coreRouter']
        hwSwitch.props['dpid'] = dpid.encodeDPID(location=popname,
                                                 vendor=dpid.Vendors.Corsa,
                                                 role=dpid.Roles.POPHwSwitch,
                                                 id=1)
        swSwitch.props['dpid'] = dpid.encodeDPID(location=popname,
                                                 vendor=dpid.Vendors.OVS,
                                                 role=dpid.Roles.POPSwSwitch,
                                                 id=1)
        self.addSwitch(hwSwitch)
        self.addSwitch(coreRouter)
        self.addSwitch(swSwitch)
        self.addHost(pop.props['serviceVm'])
        self.popIndex[popname] = pop
        for l in links:
            (n1,p1,n2,p2,type) = (self.switchIndex[l[0]],
                                  Port(l[1]),
                                  self.switchIndex[l[2]],
                                  Port(l[3]),
                                  l[4])
            p1.props['node'] = n1
            n1.props['ports'][p1.name] = p1
            p2.props['node'] = n2
            n2.props['ports'][p2.name] = p2
            link = Link(ports=[p1,p2])
            link.props['type'] = type
            if hwSwitch.name == n1.name and swSwitch.name == n2.name:
                link.setPortType('HwToSw.WAN', 'SwToHw.WAN')
            elif hwSwitch.name == n2.name and swSwitch.name == n1.name:
                link.setPortType('SwToHw.WAN', 'HwToSw.WAN')
            elif hwSwitch.name == n1.name and coreRouter.name == n2.name:
                link.setPortType('HwToCore.WAN', 'CoreToHw.WAN')
            elif hwSwitch.name == n2.name and coreRouter.name == n1.name:
                link.setPortType('CoreToHw.WAN', 'HwToCore.WAN')
            self.addLink(link)

    def getLink(self,n1,p1,n2,p2,vlan):
        for link in self.linkIndex.values():
            endpoints = link.props['endpoints']
            v = link.props['vlan']
            port1 = endpoints[0]
            port2 = endpoints[1]
            node1 = port1.props['node']
            node2 = port2.props['node']
            if (node1.name,port1.name,node2.name,port2.name,v) == (n1,p1,n2,p2,vlan):
                return link
        return None

    def getLinksByType(self,type1,type2,ordered=False):
        res = {}
        for link in self.linkIndex.values():
            if link.getPortType() == (type1,type2):
                res[link.name] = link
                continue
            if not ordered and link.getPortType() == (type2,type1):
                res[link.name] = link
                continue
        return res

    def getPopLinks(self,pop1,pop2):
        res = {}
        coreRouter1 = pop1.props['coreRouter']
        hwSwitch1 = pop1.props['hwSwitch']
        swSwitch1 = pop1.props['swSwitch']
        coreRouter2 = pop2.props['coreRouter']
        vlan = 0
        # Retrieve Core to Core OSCARS VLAN
        for link in self.linkIndex.values():
            if not 'gri' in link.props:
                continue
            endpoints = link.props['endpoints']
            node1 = endpoints[0].props['node']
            node2 = endpoints[1].props['node']
            if node1.name == coreRouter1.name and node2.name == coreRouter2.name:
                vlan = link.props['vlan']
                break
        # Retrieve corresponding CoreToHw link
        links = self.getLinksByType('CoreToHw.WAN', 'HwToCore.WAN')
        for link in links.values():
            if not 'core' in link.props['type']:
                continue
            endpoints = link.props['endpoints']
            node1 = endpoints[0].props['node']
            node2 = endpoints[1].props['node']
            if node1.name == coreRouter1.name and node2.name == hwSwitch1.name:
                res[link.name] = Link(ports=link.props['endpoints'],
                                             vlan=vlan,
                                             props=link.props)
                break
            if node2.name == coreRouter1.name and node1.name == hwSwitch1.name:
                reverseLink = link.props['reverseLink']
                res[reverseLink.name] = Link(ports=reverseLink.props['endpoints'],
                                             vlan=vlan,
                                             props=reverseLink.props)
                break
        # Retrieve corresponding HwToSw link
        links = self.getLinksByType('SwToHw.WAN','HwToSw.WAN')
        for link in links.values():
            if not 'hw' in link.props['type']:
                continue
            endpoints = link.props['endpoints']
            node1 = endpoints[0].props['node']
            node2 = endpoints[1].props['node']
            if node1.name == swSwitch1.name and node2.name == hwSwitch1.name:
                reverseLink = link.props['reverseLink']
                res[reverseLink.name] = Link(ports=reverseLink.props['endpoints'],
                                             vlan=vlan,
                                             props=reverseLink.props)
                break
            if node1.name == swSwitch1.name and node2.name == hwSwitch1.name:
                res[link.name] = Link(ports=link.props['endpoints'],
                                      vlan=vlan,
                                      props=link.props)
                break
        return res

    def updateSwitch(self, switch):
        role = switch.get('role')
        if role: # hwSwitch, coreRouter, swSwitch
            switch.update({'controller':self.controller})


    def displaySwitches(self):
        print "\nName\t\t\tDPID\t\tODL Name\n"
        for sw in self.siteIndex.values():
            if 'dpid' in sw.props:
                hexdpid = binascii.hexlify(sw.props['dpid'])
                print sw.name,"\t",hexdpid,"\topenflow:" + str(int(hexdpid,16))
        print "\n\n"

    def loadDefault(self):

        # init self.pops
        for location in self.locations:
            (popname, hwswitchname, coreroutername, swswitchname,links) = (location[0],
                                                                           location[1],
                                                                           location[2],
                                                                           location[0] + "-ovs",
                                                                           location[3]
                                                                           )

            self.addSDNPop(popname, hwswitchname, coreroutername, swswitchname,links)

        # create mesh between core routers, attached to VLANs between the core routers and hardware switches
        for l in corecircuits:
            (gri,srcURN,dstURN,vlan) = l
            (srcNodeName,srcDomain,srcPortName,srcLink) = oscars.parseURN(srcURN)
            (dstNodeName,dstDomain,dstPortName,dstLink)  = oscars.parseURN(dstURN)
            # By convention, the source is always the router connected to the host. We do not yet know this
            # switch, therefore we need to create it.
            srcNode = self.switchIndex[srcNodeName]
            srcPort = srcNode.props['ports'][srcPortName]
            dstNode = self.switchIndex[dstNodeName]
            dstPort = dstNode.props['ports'][dstPortName]
            link = Link(ports=[srcPort,dstPort],vlan=vlan)
            link.props['gri'] = gri
            self.addLink(link)

        # Add sites to the topology
        for (siteName,hosts,pop) in sites:
            site = Site(siteName)
            self.siteIndex[siteName] = site
            (siteName,gri,srcURN,dstURN,vlan) = sitecircuits[siteName]
            (srcNodeName,srcDomain,srcPortName,srcLink) = oscars.parseURN(srcURN)
            (dstNodeName,dstDomain,dstPortName,dstLink)  = oscars.parseURN(dstURN)
            # By convention, the source is always the router where the host directly connects to.
            srcNode = Switch(srcNodeName)
            self.addSwitch(srcNode)
            srcPort = Port(srcPortName)
            srcNode.addPort(srcPort)
            dstNode = self.switchIndex[dstNodeName]
            dstPort = dstNode.props['ports'][dstPortName]
            link = Link(ports=[srcPort,dstPort],vlan=vlan)
            site.props['SiteToCore'] = link
            site.addSwitch(srcNode)
            #self.addLink(link)

            for h in hosts:
                host = Host(h)
                # Host are directly connected to core router. Build a link. Each host is connected using eth2
                srcHostPort = Port("eth2")
                srcHostPort.props['node'] = host
                link = Link(ports=[srcHostPort,srcPort],vlan=vlan)
                self.addLink(link)
                site.addHost(host=host,link=link)

        self.wan.connectAll(self.popIndex.values())

        for switch in self.switchIndex.values():
            self.updateSwitch(switch)

    def loadConfiguration(self,fileName):
        """
        loads the topology Mininet needs to create as described in a file. The format is a dictionary with
        the following structure:


        :param fileName:
        :return:
        """
        f = open(fileName,"r")
        self.config = eval (f.read())
        f.close()

if __name__ == '__main__':
    topo = TopoBuilder()
    topo.displaySwitches()


	
