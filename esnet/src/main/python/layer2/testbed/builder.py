#!/usr/bin/python
#
# ENOS, Copyright (c) 2015, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov.
#
# NOTICE.  This software is owned by the U.S. Department of Energy.  As such,
# the U.S. Government has been granted for itself and others acting on its
# behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software
# to reproduce, prepare derivative works, and perform publicly and display
# publicly.  Beginning five (5) years after the date permission to assert
# copyright is obtained from the U.S. Department of Energy, and subject to
# any subsequent five (5) year renewals, the U.S. Government is granted for
# itself and others acting on its behalf a paid-up, nonexclusive, irrevocable,
# worldwide license in the Software to reproduce, prepare derivative works,
# distribute copies to the public, perform publicly and display publicly, and
# to permit others to do so.
#

import struct,binascii
from array import array

from layer2.common.api import Node, SDNPop, Link, Port, Site, Wan, VPN, Host, HwSwitch, SwSwitch, Switch
from layer2.common.mac import MACAddress
from layer2.testbed import dpid, oscars

from layer2.common.utils import Logger

# All switches including site routers, core routers, hw switches, and sw switches should
# not have the same name so that the name of each port could be unique.
# site = [siteRouterName, [hostNames], popName, portNo]
# Note: Since flowmod could not forward a packet to where it comes from,
#  multiple sites in the same pop must have different portNo! (otherwise, the broadcast won't work.)

# Simulated sites ESnet production diskpt's
lblsite = ["lbl.gov",['lbl-diskpt1@lbl.gov'],"denv"]
anlsite = ["anl.gov",['anl-diskpt1@anl.gov'],"star"]
bnlsite = ["bnl.gov",['bnl-diskpt1@bnl.gov'],"aofa"]
washsite = ["site1.wash",['wash-tbn-1@site1.wash'],"wash"]
asmtsite = ["site2.amst",['amst-tbn-1@site2.asmt'],"amst"]
cernsite = ["site3.cern",['cern-272-tbn-1@site3.cern'],"cern"]
sites = [lblsite, anlsite, bnlsite]

# DENV
denvlinks=[
    ["denv-cr5","9/1/4","denv-tb-of-1","23",'core'],
    ["denv-cr5","9/1/5","denv-tb-of-1","24",'site'],
    ["denv-ovs","eth10","denv-tb-of-1","1",'hw'],
    ["denv-ovs","eth11","denv-tb-of-1","2",'none']
]
denv=["denv",'denv-tb-of-1',"denv-cr5","denv-ovs",denvlinks]


# WASH
washlinks = [
    ["wash-cr5","10/1/11","wash-tb-of-1","23",'core'],
    ["wash-cr5","10/1/12","wash-tb-of-1","24",'site'],
    ["wash-ovs","eth10","wash-tb-of-1","1",'hw'],
    ["wash-tbn-1","eth11","wash-tb-of-1","2",'none']
]
washlinks_demo = [
    ["wash-cr5","10/1/12","wash-tb-of-1","24",'core'],
    ["wash-cr5","10/1/11","wash-tb-of-1","2",'site'],  # FAKE
    ["wash-ovs","eth10","wash-tb-of-1","1",'hw']
]

wash=["wash",'wash-tb-of-1',"wash-cr5","wash-ovs", washlinks]

# AOFA
aofalinks = [
    ["aofa-cr5","10/1/3","aofa-tb-of-1","23",'core'],
    ["aofa-cr5","10/1/4","aofa-tb-of-1","24",'site'],
    ["aofa-ovs","eth10","aofa-tb-of-1","1",'hw'],
    ["aofa-ovs","eth11","aofa-tb-of-1","2",'none']
]
aofa=["aofa",'aofa-tb-of-1',"aofa-cr5","aofa-ovs",aofalinks]

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
    ["amst-tbn-1","eth17","amst-tb-of-1","8",'none']
]

amstlinks_demo = [
    ["amst-cr5","10/1/3","amst-tb-of-1","17",'core'],
    ["amst-cr5","10/1/4","amst-tb-of-1","8",'site'],     # FAKE
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
    ["amst-ovs","eth16","amst-tb-of-1","7",'none']
]
amst=["amst",'amst-tb-of-1',"amst-cr5","amst-ovs",amstlinks]

# CERN
cernlinks = [
    ["cern-272-cr5","10/1/4","cern-272-tb-of-1","20",'site'],
    ["cern-272-cr5","10/1/5","cern-272-tb-of-1","21",'core'],
    ["cern-272-cr5","10/1/6","cern-272-tb-of-1","22",'core'],
    ["cern-272-cr5","10/2/5","cern-272-tb-of-1","23",'none'],
    ["cern-272-cr5","10/2/6","cern-272-tb-of-1","24",'none'],
    ["cern-272-ovs","eth10","cern-272-tb-of-1","1",'hw'],
    ["cern-272-ovs","eth11","cern-272-tb-of-1","2",'none'],
    ["cern-272-ovs","eth12","cern-272-tb-of-1","3",'none'],
    ["cern-272-ovs","eth13","cern-272-tb-of-1","4",'none'],
    ["cern-272-tbn-1","eth14","cern-272-tb-of-1","5",'none']
]

cernlinks_demo = [
    ["cern-272-cr5","10/1/4","cern-272-tb-of-1","5",'site'],  # FAKE
    ["cern-272-cr5","10/1/5","cern-272-tb-of-1","21",'none'],
    ["cern-272-cr5","10/1/6","cern-272-tb-of-1","22",'none'],
    ["cern-272-cr5","10/2/5","cern-272-tb-of-1","23",'core'],
    ["cern-272-cr5","10/2/6","cern-272-tb-of-1","24",'core'],
    ["cern-272-ovs","eth10","cern-272-tb-of-1","1",'hw'],
    ["cern-272-ovs","eth11","cern-272-tb-of-1","2",'none'],
    ["cern-272-ovs","eth12","cern-272-tb-of-1","3",'none'],
    ["cern-272-ovs","eth13","cern-272-tb-of-1","4",'none']
]
cern=["cern",'cern-272-tb-of-1',"cern-272-cr5","cern-272-ovs",cernlinks]

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
atla=["atla",'atla-tb-of-1',"atla-cr5","atla-ovs",atlalinks]

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
star=["star",'star-tb-of-1',"star-cr5","star-ovs",starlinks]

# LBL  POP is not yet deployed

# CORE TO CORE OSCARS circuits
#  GRI,src,dest,vlan.
corecircuits = [
    # DENV - STAR - AOFA 1Mbps + scavenger
    ['es.net-5909',
     'urn:ogf:network:domain=es.net:node=denv-cr5:port=9/1/4:link=*',
     'urn:ogf:network:domain=es.net:node=aofa-cr5:port=10/1/3:link=*',
     582] ,
    ['es.net-5972',
     'urn:ogf:network:domain=es.net:node=star-cr5:port=9/2/3:link=*',
     'urn:ogf:network:domain=es.net:node=denv-cr5:port=9/1/4:link=*',
     2953],
    ['es.net-5971',
     'urn:ogf:network:domain=es.net:node=star-cr5:port=9/2/3:link=*',
     'urn:ogf:network:domain=es.net:node=aofa-cr5:port=10/1/3:link=*',
     4054],
    # WASH - AMST - CERN 9.5Gbps on WASH - CERN and AMST - CERN, 1Mbps on WASH - AMST

    ['es.net-5954',
     'urn:ogf:network:domain=es.net:node=wash-cr5:port=10/1/12:link=*',
    'urn:ogf:network:domain=es.net:node=cern-272-cr5:port=10/2/5:link=*',
     1232],
    ['es.net-5956',
     'urn:ogf:network:domain=es.net:node=wash-cr5:port=10/1/12:link=*',
     'urn:ogf:network:domain=es.net:node=amst-cr5:port=10/2/4:link=*',
     3905],
    ['es.net-5955',
     'urn:ogf:network:domain=es.net:node=cern-272-cr5:port=10/2/5:link=*',
     'urn:ogf:network:domain=es.net:node=amst-cr5:port=10/2/4:link=*',
     3970]
]

# SITE to SDN POP OSCARS circuits
#  Site,GRI,src,dest,vlan
# By convention, the source is always the router connected to the  host and the destination is
#  always the core router connected to the SDN POP.
sitecircuits = {}

sitecircuits['lbl.gov'] = \
    ['lbl.gov',
     'es.net-5924',
     'urn:ogf:network:domain=es.net:node=lbl-mr2:port=xe-9/3/0:link=*',
     'urn:ogf:network:domain=es.net:node=denv-cr5:port=9/1/5:link=*',
     1994]

sitecircuits['anl.gov'] = \
    ['anl.gov',
     'es.net-5969',
     'urn:ogf:network:domain=es.net:node=anl-mr2:port=xe-1/2/0:link=*',
     'urn:ogf:network:domain=es.net:node=star-cr5:port=9/2/4:link=*',
     3572]

sitecircuits['bnl.gov'] = \
    ['bnl.gov',
     'es.net-5925',
     'urn:ogf:network:domain=es.net:node=bnl-mr2:port=xe-2/2/0:link=*',
     'urn:ogf:network:domain=es.net:node=aofa-cr5:port=10/1/4:link=*',
     116]

# The following are simulated links
"""
Fake sites for VPN code
sitecircuits['site1.wash'] = \
    ['site1.wash',
     'es.net-fake1',
     'urn:ogf:network:domain=site1.wash:node=wash:port=xe-9/3/0:link=*',
     'urn:ogf:network:domain=es.net:node=wash-cr5:port=10/1/12:link=*',
     100]

sitecircuits['site2.amst'] = \
    ['site2.amst',
     'es.net-fake2',
     'urn:ogf:network:domain=site2.amst:node=amst:port=xe-9/3/0:link=*',
     'urn:ogf:network:domain=es.net:node=amst-cr5:port=10/1/4:link=*',
     100]

sitecircuits['site3.cern'] = \
    ['site3.cern',
     'es.net-fake3',
     'urn:ogf:network:domain=site3.cern:node=cern:port=xe-9/3/0:link=*',
     'urn:ogf:network:domain=es.net:node=cern-272-cr5:port=10/1/4:link=*',
     100]
"""
sitecircuits['site1.wash'] = \
    ['site1.wash',
     'es.net-fake1',
     'urn:ogf:network:domain=site1.wash:node=wash-tbn-1:port=eth11:link=*',
     'urn:ogf:network:domain=es.net:node=wash-tb-of-1:port=2:link=*',
     100]

sitecircuits['site2.amst'] = \
    ['site2.amst',
     'es.net-fake2',
     'urn:ogf:network:domain=site2.amst:node=amst-tbn-1:port=eth17:link=*',
     'urn:ogf:network:domain=es.net:node=amst-tb-of-1:port=8link=*',
     100]

sitecircuits['site3.cern'] = \
    ['site3.cern',
     'es.net-fake3',
     'urn:ogf:network:domain=site3.cern:node=cern-272-tbn-1:port=eth14:link=*',
     'urn:ogf:network:domain=es.net:node=cern-272-tb-of-1:port=5:link=*',
     100]


# SDN POP's
locations=[denv,wash,aofa,amst,cern,atla,star]
testbedPops = {"denv":denv,"wash":wash,"aofa":aofa,"amst":amst,"cern":cern,"atla":atla,"star":star}

class TopoBuilder ():

    debug = False;
    logger = Logger('TopoBuilder')

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
        if link.name in self.linkIndex:
            TopoBuilder.logger.error("link duplicate %s" % link.name)
            return
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

    def addSite(self,popname,site):
        self.siteIndex[site.name] = site
        pop = self.popIndex[popname]
        site.setPop(pop)
        links = self.getSiteOSCARSLinks(site)
        # print "TopoBuilder.addSite " + site.name + " pop " + pop.name + " links " + str(links)
        pop.addSite(site, links)

    def addSDNPop(self, popname, hwswitchname, coreroutername, swswitchname,links):
        """
        Configure the various elements of an SDN POP
        :param popname: Name of POP
        :param hwswitchname: Name of hardware SDN switch
        :param coreroutername: Name of core router
        :param swswitchname: Name of software SDN switch
        :param links: Set of physical links within the POP
        :return: None
        """
        pop = SDNPop(name=popname,
                     hwswitchname=hwswitchname,
                     coreroutername=coreroutername,
                     swswitchname=swswitchname)

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

        hwLinks = []
        swLinks = []

        for l in links:
            # Following is slightly a workaround: this class is currently used by two different topology, one with
            # sites on remote hosts, the other using the testbed hosts as site.
            srcNode = None
            dstNode = None
            if '-tbn-' in l[0]:
                # This is a testbed host. We need to create it and add it
                host = Host(l[0])
                self.addHost(host)
                srcNode = host
            else:
                srcNode = self.switchIndex[l[0]]
            if '-tbn-' in l[2]:
                # This is a testbed host. We need to create it and add it
                host = Host(l[2])
                self.addHost(host)
                dstNode = host
            else:
                dstNode = self.switchIndex[l[2]]
            (n1,p1,n2,p2,type) = (srcNode,
                                  Port(l[1]),
                                  dstNode,
                                  Port(l[3]),
                                  l[4])
            p1.props['node'] = n1
            n1.props['ports'][p1.name] = p1
            p2.props['node'] = n2
            n2.props['ports'][p2.name] = p2
            link = Link(ports=[p1,p2])
            link.props['type'] = type

            if hwSwitch.name == n1.name and swSwitch.name == n2.name:
                # Tag hardware and software switch ports according to
                # whether they're supposed to be used for WAN traffic
                # or site traffic.  WAN ports have links with type 'hw'.
                # We need to set port types differently because we
                # match PACKET_IN events with their scopes differently
                # depending on whether the port corresponds to a WAN trunk
                # (need to use VLAN ID of translated MAC addresses to
                # demultiplex packets) or a site link (use VLAN ID to
                # demultiplex packets to scopes).
                if type == 'hw':
                    link.setPortType('HwToSw.WAN', 'SwToHw.WAN')
                else:
                    link.setPortType('HwToSw', 'SwToHw')
                swLinks.append(link)
            elif hwSwitch.name == n2.name and swSwitch.name == n1.name:
                # See above comment about setting the types of switch
                # ports and why we need to do this.
                if type == 'hw':
                    link.setPortType('SwToHw.WAN', 'HwToSw.WAN')
                else:
                    link.setPortType('SwToHw', 'HwToSw')
                swLinks.append(link)
            elif hwSwitch.name == n1.name and coreRouter.name == n2.name:
                # Tag the hardware switch ports according to whether they're
                # facing the site (through the core) or facing the wan (again
                # through the core).  This is only available from the link.
                # This distinction needs to be made because we match
                # up inbound PACKET_IN events with containing scopes in
                # different ways.
                if type == 'site':
                    link.setPortType('HwToCore', 'CoreToHw')
                else:
                    link.setPortType('HwToCore.WAN', 'CoreToHw.WAN')
                hwLinks.append(link)
            elif hwSwitch.name == n2.name and coreRouter.name == n1.name:
                # See above comment about tagging the hardware switch ports.
                if type == 'site':
                    link.setPortType('CoreToHw', 'HwToCore')
                else:
                    link.setPortType('CoreToHw.WAN', 'HwToCore.WAN')
                hwLinks.append(link)
            self.addLink(link)
        index = 0
        for link in hwLinks:
            if index == len(swLinks):
                break
#            print "TopoBuilder.addSDNPop pop " + pop.name + " hw " + link.name + " sw " + swLinks[index].name
            pop.addLinks(hwlink=link,swlink=swLinks[index])
            index += 1


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

    def getSiteOSCARSLinks(self,site):
        res = {}
        for link in self.linkIndex.values():
            if not 'gri' in link.props:
                continue
            endpoints = link.props['endpoints']
            node1 = endpoints[0].props['node']
            node2 = endpoints[1].props['node']
            if site.name == node2.props['domain']:
                # Only keep links that points to the site
                res[link.name] = link
        return res

    def getPopLinks(self,pop1,pop2):
        """
        Given a pair of POPs, locate the OSCARS circuit (if any) that connects their
        core routers.  Then using the VLAN tag from that OSCARS circuit, create two links
        parallel to the physical links connecting the hardware switch to the core,
        and connecting the software switch to the hardware switch.  The newly-created
        links have information about the OSCARS GRI and POPs.
        :param pop1: POP for which we're creating VLAN links
        :param pop2: Remote POP
        :return: array of links
        """
        res = {}
        coreRouter1 = pop1.props['coreRouter']
        hwSwitch1 = pop1.props['hwSwitch']
        swSwitch1 = pop1.props['swSwitch']
        coreRouter2 = pop2.props['coreRouter']
        vlan = 0
        gri = ''
        # Retrieve Core to Core OSCARS VLAN
        for link in self.linkIndex.values():
            if not 'gri' in link.props:
                continue
            endpoints = link.props['endpoints']
            node1 = endpoints[0].props['node']
            node2 = endpoints[1].props['node']
            gri = link.props['gri']
            if node1.name == coreRouter1.name and node2.name == coreRouter2.name:
                vlan = link.props['vlan']
                # Only look for links with non-zero VLANs since all valid OSCARS circuits have non-zero
                # VLAN tags
                if vlan > 0:
                    break
        # If we didn't find an inter-POP link, then we're done...don't create any other links within the POP
        if vlan == 0:
            return res
        # We want to store the POPs into the links
        pops = [ pop1, pop2 ]
        # Retrieve corresponding CoreToHw link and create a new link for the plumbed VLAN
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
                res[link.name].props['pops'] = pops
                res[link.name].props['gri'] = gri
                break
            if node2.name == coreRouter1.name and node1.name == hwSwitch1.name:
                reverseLink = link.props['reverseLink']
                res[reverseLink.name] = Link(ports=reverseLink.props['endpoints'],
                                             vlan=vlan,
                                             props=reverseLink.props)
                res[reverseLink.name].props['pops'] = pops
                res[reverseLink.name].props['gri'] = gri
                break
        # Retrieve corresponding HwToSw link and create a new link for the plumbed VLAN
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
                res[reverseLink.name].props['pops'] = pops
                res[reverseLink.name].props['gri'] = gri
                break
            if node1.name == swSwitch1.name and node2.name == hwSwitch1.name:
                res[link.name] = Link(ports=link.props['endpoints'],
                                      vlan=vlan,
                                      props=link.props)
                res[link.name].props['pops'] = pops
                res[link.name].props['gri'] = gri
                break
        return res

    def updateSwitch(self, switch):
        role = switch.get('role')
        if role: # hwSwitch, coreRouter, swSwitch
            switch.update({'controller':self.controller})


    def displaySwitches(self):
        print "\nName\t\t\tDPID\t\tODL Name\n"
        for sw in self.switchIndex.values():
            if 'dpid' in sw.props:
                hexdpid = binascii.hexlify(sw.props['dpid'])
                print sw.name,"\t",hexdpid,"\topenflow:" + str(int(hexdpid,16))
        print "\n\n"

    def getSite(self,siteName):
        if siteName in self.siteIndex.keys():
            return self.siteIndex[siteName]
        return None

    def loadDefault(self):

        # init self.pops
        for location in self.locations:
            (popname, hwswitchname, coreroutername, swswitchname,links) = (location[0],
                                                                           location[1],
                                                                           location[2],
                                                                           location[3],
                                                                           location[4]
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
            srcNode.addLink(link)
            dstNode.addLink(link)

        # Add sites to the topology
        for (siteName,hosts,pop) in sites:
            site = Site(siteName)
            (siteName,gri,srcURN,dstURN,vlan) = sitecircuits[siteName]
            (srcNodeName,srcDomain,srcPortName,srcLink) = oscars.parseURN(srcURN)
            (dstNodeName,dstDomain,dstPortName,dstLink)  = oscars.parseURN(dstURN)
            # By convention, the source is always the router where the host directly connects to.
            srcNode = Switch(srcNodeName,domain=siteName)
            self.addSwitch(srcNode)
            srcPort = Port(srcPortName)
            srcNode.addPort(srcPort)
            dstNode = self.switchIndex[dstNodeName]
            dstPort = dstNode.props['ports'][dstPortName]
            link = Link(ports=[srcPort,dstPort],vlan=vlan)
            link.props['gri'] = gri
            site.props['SiteToCore'] = link
            self.addLink(link)
            site.addSwitch(srcNode)
            self.addSite(site=site,popname=pop)

            for h in hosts:
                host = Host(h,domain=siteName)
                # Host are directly connected to core router. Build a link. Each host is connected using eth2
                srcHostPort = Port("eth2")
                srcHostPort.props['node'] = host
                link = Link(ports=[srcHostPort,srcPort],vlan=vlan)
                self.addLink(link)
                site.addHost(host=host,link=link)
                self.addHost(host)

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


	
