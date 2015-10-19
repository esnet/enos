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
import threading
import random

class Properties(object):
    def __init__(self, name,props={}):
        self.name = name
        self.props = {}
        self.update(props)
    def update(self, props):
        self.props.update(props)
    def get(self, prop):
        if prop in self.props:
            return self.props[prop]
        else:
            # suggest to complain by Logger
            return None
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name

class Port(Properties):
    def __init__(self,name,props={}):
        super(Port, self).__init__(name)
        # configured by Node:
        self.props['node'] = None # Node
        self.props['interfaceIndex'] = 0
        # configured by Link:
        self.props['links'] = [] # list of Link
        # Others
        self.props['scopeIndex'] = {} # [vid] = Scope
        self.props['vlan'] = 0
        self.update(props)
    def __repr__(self):
        return 'Port(name=%s, interfaceIndex=%d, vlan=%d)' % (self.name, self.props['interfaceIndex'], self.props['vlan'])

class Node(Properties):
    def __init__(self, name, props={}):
        super(Node, self).__init__(name)
        self.props['ports'] = {} # [interfaceIndex] = Port
        self.interfaceIndex = 1
        self.update(props)
    def getPort(self, interfaceIndex):
        # create new port if interfaceIndex == 0
        if interfaceIndex == 0:
            interfaceIndex = self.interfaceIndex
            self.interfaceIndex += 1
        if not interfaceIndex in self.props['ports']:
            port = Port(name='%s-eth%s' % (self.name, interfaceIndex))
            port.update({'node' : self, 'interfaceIndex' : interfaceIndex})
            self.props['ports'][interfaceIndex] = port
        return self.props['ports'][interfaceIndex]

class Host(Node):
    def __init__(self, name, props={}):
        super(Host, self).__init__(name)
        self.props['site'] = None # Site
        self.props.update(props)
    def setSite(self, site):
        self.props['site'] = site
class ServiceVm(Node):
    def __init__(self, name, props={}):
        super(ServiceVm, self).__init__(name)
        self.props['role'] = 'ServiceVm'
        self.update(props)

class Switch(Node):
    def __init__(self, name, props={}):
        super(Switch, self).__init__(name, props=props)

class SiteRouter(Switch):
    def __init__(self, name, props={}):
        super(SiteRouter, self).__init__(name, props=props)
        self.props['role'] = 'SiteRouter'
        self.props['toWanPort'] = None # Port
        self.props['hostPortIndex'] = {} # [hostname] = Port
    def setWanLink(self, link):
        self.props['toWanPort'] = link.props['portIndex'][self.name]
    def addHost(self, host, link):
        self.props['hostPortIndex'][host.name] = link.props['portIndex'][self.name]
class CoreRouter(Switch):
    def __init__(self, name, props={}):
        super(CoreRouter, self).__init__(name)
        self.props['role'] = 'CoreRouter'
        self.props['pop'] = None
        self.props['toHwPorts'] = [] # nbOfLinks 'CoreToHw' ports
        self.props['stitchedPortIndex'] = {} # [lanport.name] = stitched port (to hw)
        self.props['stitchedPortIndex.WAN'] = {} # [wanport.name] = stitched port (to hw or to wan) (2 ways)
        self.props['sitePortIndex'] = {} # [sitename] = tosite_port
        self.props['wanPortIndex'] = {} # [popname] = towan_port
        self.props.update(props)
    def addSite(self, site, link, portno):
        to_site_port = link.props['portIndex'][self.name] # CoreToSite
        to_hw_port = self.props['toHwPorts'][portno] # CoreToHw
        self.props['sitePortIndex'][site.name] = to_site_port
        self.props['stitchedPortIndex'][to_site_port.name] = to_hw_port
    def connectPop(self, pop, wanlink, hwlink):
        """

        :param pop:
        :param wanlink: CoreToCore
        :param hwlink:  CoreToHw
        :return:
        """
        wanport = wanlink.props['portIndex'][self.name]
        hwport = hwlink.props['portIndex'][self.name]
        self.props['wanPortIndex'][pop.name] = wanport
        self.props['stitchedPortIndex.WAN'][wanport.name] = hwport
        self.props['stitchedPortIndex.WAN'][hwport.name] = wanport
    def addLink(self, hwlink):
        self.props['toHwPorts'].append(hwlink.props['portIndex'][self.name])

class HwSwitch(Switch):
    def __init__(self, name, props={}):
        super(HwSwitch, self).__init__(name, props=props)
        self.props['role'] = 'HwSwitch'
        self.props['toCorePorts'] = [] # list of Port toward to coreRouter
        self.props['toSwPorts'] = [] # list of Port toward to swSwitch
        self.props['stitchedPortIndex'] = {} # [(hw|sw)_port.name] = (sw|hw)_port
        self.props['pop'] = None
        self.props['sitePortIndex'] = {} # [sitename] = stitched port to core
        self.props['wanPortIndex'] = {} # [pop.name] = Port
    def addSite(self, site, portno):
        self.props['sitePortIndex'][site.name] = self.props['toCorePorts'][portno]
    def connectPop(self, pop, hwlink, swlink):
        """

        :param pop:
        :param hwlink:   CoreToHw
        :param swlink:   HwToSw
        :return:
        """
        self.props['wanPortIndex'][pop.name] = hwlink.props['portIndex'][self.name]
        hwport = hwlink.props['portIndex'][self.name]
        swport = swlink.props['portIndex'][self.name]
        self.props['stitchedPortIndex'][hwport.name] = swport
        self.props['stitchedPortIndex'][swport.name] = hwport
    def addLink(self, hwlink, swlink):
        hwport = hwlink.props['portIndex'][self.name]
        swport = swlink.props['portIndex'][self.name]
        self.props['toCorePorts'].append(hwport)
        self.props['toSwPorts'].append(swport)
        self.props['stitchedPortIndex'][hwport.name] = swport
        self.props['stitchedPortIndex'][swport.name] = hwport

class SwSwitch(Switch):
    def __init__(self, name, props={}):
        super(SwSwitch, self).__init__(name, props=props)
        self.props['role'] = 'SwSwitch'
        self.props['wanPortIndex'] = {} # [pop.name] = Port
        self.props['sitePortIndex'] = {} # [site.name] = Port
        self.props['vmPort'] = None # Port to serviceVm
        self.props['vmPort.WAN'] = None # Port to serviceVm
        self.props['toHwPorts'] = [] # list of Port to hwSwitch
        self.props['pop'] = None
    def addSite(self, site, portno):
        self.props['sitePortIndex'][site.name] = self.props['toHwPorts'][portno]
    def connectPop(self, pop, link):
        """

        :param pop:
        :param link:   HwToSw
        :return:
        """
        self.props['wanPortIndex'][pop.name] = link.props['portIndex'][self.name]
    def addLink(self, swlink):
        self.props['toHwPorts'].append(swlink.props['portIndex'][self.name])
    def connectServiceVm(self, sitelink, wanlink):
        self.props['vmPort'] = sitelink.props['portIndex'][self.name]
        self.props['vmPort.WAN'] = wanlink.props['portIndex'][self.name]

class SDNPop(Properties):
    def __init__(self, name, hwswitchname, coreroutername, swswitchname, nbOfLinks=1, props={}):
        super(SDNPop, self).__init__(name, props=props)
        self.props['sites'] = []
        self.props['links'] = []
        hwSwitch = HwSwitch(hwswitchname)
        hwSwitch.props['pop'] = self
        coreRouter = CoreRouter(coreroutername)
        coreRouter.props['pop'] = self
        swSwitch = SwSwitch(swswitchname)
        swSwitch.props['pop'] = self
        serviceVm = ServiceVm('%s-vm' % self.name)

        # create LAN links between coreRouter and hwSwitch
        for i in range(nbOfLinks):
            vlan = i + 1
            hwlink = Link.create(coreRouter, hwSwitch, vlan)
            hwlink.setPortType('CoreToHw', 'HwToCore')
            swlink = Link.create(hwSwitch, swSwitch, vlan)
            swlink.setPortType('HwToSw', 'SwToHw')
            coreRouter.addLink(hwlink)
            hwSwitch.addLink(hwlink, swlink)
            swSwitch.addLink(swlink)
            self.props['links'].extend([hwlink, swlink])
        # create links between swSwitch and serviceVm
        sitelink = Link.create(serviceVm, swSwitch)
        sitelink.setPortType('SwToVm', 'VmToSw')
        self.props['links'].append(sitelink)
        wanlink = Link.create(serviceVm, swSwitch)
        wanlink.setPortType('SwToVm.WAN', 'VmToSw.WAN')
        self.props['links'].append(wanlink)
        swSwitch.connectServiceVm(sitelink, wanlink)

        self.props['hwSwitch'] = hwSwitch
        self.props['coreRouter'] = coreRouter
        self.props['swSwitch'] = swSwitch
        self.props['serviceVm'] = serviceVm
        self.props['nbOfLinks'] = nbOfLinks
    def addSite(self, site, link, portno):
        self.props['coreRouter'].addSite(site, link, portno)
        self.props['hwSwitch'].addSite(site, portno)
        self.props['swSwitch'].addSite(site, portno)
        self.props['sites'].append(site)
    def connectPop(self, pop, link, vlan):
        """

        :param pop:
        :param link:   CoreToCore link
        :param vlan:   Core - HwSwitch VLAN
        :return:
        """
        # hw[tocore_port] --<hwlink>-- [core_port]core[wanPort] --<wanlink with vlan>-- pop
        coreRouter = self.props['coreRouter']
        hwSwitch = self.props['hwSwitch']
        hwlink = Link.create(coreRouter, hwSwitch, vlan)
        hwlink.setPortType('CoreToHw.WAN', 'HwToCore.WAN')
        coreRouter.connectPop(pop, link, hwlink)
        # sw[tohw_port] --<swlink>-- [tosw_port]hw
        swSwitch = self.props['swSwitch']
        swlink = Link.create(hwSwitch, swSwitch, vlan)
        swlink.setPortType('HwToSw.WAN', 'SwToHw.WAN')
        hwSwitch.connectPop(pop, hwlink, swlink)
        swSwitch.connectPop(pop, swlink)
        return (hwlink, swlink)
class VPN(Properties):
    VERSION = 1
    vids = [] # existed vid
    lock = threading.Lock()
    def __init__(self, name, vid=None, props={}):
        super(VPN, self).__init__(name, props=props)
        with VPN.lock:
            if not vid:
                vid = random.randint(1, 2**24)
                while vid in VPN.vids:
                    vid = random.randint(1, 2**24)
            self.props['vid'] = vid # int
            VPN.vids.append(vid)
        self.props['participants'] = [] # list of (site, hosts, lanVlan, siteVlan)
        self.props['participantIndex'] = {} # [sitename] = (site, hosts, lanVlan, siteVlan)
        self.props['siteIndex'] = {} # [hwToCorePort.siteVlan] = site
        self.props['mat'] = None # MAC Address Translation
        self.props['renderer'] = None # SDNPopsRenderer

    def serialize(self):
        obj = {}
        obj['version'] = VPN.VERSION
        obj['name'] = self.name
        obj['vid'] = self.props['vid']

        # store participants' name
        obj['participants'] = []
        for (site, hosts, lanVlan, siteVlan) in self.props['participants']:
            hostnames = map(lambda host:host.name, hosts)
            obj['participants'].append((site.name, hostnames, lanVlan, siteVlan))

        obj['siteIndex'] = {}
        for (key, value) in self.props['siteIndex'].items():
            obj['siteIndex'][key] = value.name

        obj['renderer'] = self.props['renderer'].serialize()
        obj['mat'] = self.props['mat'].serialize()
        return obj

    @staticmethod
    def deserialize(obj, net):
        if obj['version'] != VPN.VERSION:
            return None
        vpn = VPN(obj['name'], obj['vid'])
        for (sitename, hostnames, lanVlan, siteVlan) in obj['participants']:
            site = net.builder.siteIndex[sitename]
            hosts = map(lambda hostname:net.builder.hostIndex[hostname], hostnames)
            participant = (site, hosts, lanVlan, siteVlan)
            vpn.props['participants'].append(participant)
            vpn.props['participantIndex'][sitename] = participant
        for (key, value) in obj['siteIndex'].items():
            vpn.props['siteIndex'][key] = net.builder.siteIndex[value]
        if obj['mat']:
            from mininet.mat import MAT
            vpn.props['mat'] = MAT.deserialize(obj['mat'])
        if obj['renderer']:
            from mininet.l2vpn import SDNPopsRenderer
            vpn.props['renderer'] = SDNPopsRenderer.deserialize(obj['renderer'], vpn, net)
        return vpn

    def checkSite(self, site):
        return site.name in self.props['participantIndex']

    def addSite(self, site, lanVlan, siteVlan):
        # could be invoked in CLI
        if site.name in self.props['participantIndex']:
            return False
        pop = site.props['pop']
        participant = (site, [], lanVlan, siteVlan)
        self.props['participants'].append(participant)
        self.props['participantIndex'][site.name] = participant
        hwSwitch = pop.props['hwSwitch']
        port = hwSwitch.props['sitePortIndex'][site.name]
        self.props['siteIndex']["%s.%d" % (port.name, siteVlan)] = site
        return True

    def delSite(self, site):
        # could be invoked in CLI
        if not site.name in self.props['participantIndex']:
            return False
        siteVlan = self.props['participantIndex'][site.name][3]
        s = self.props['participantIndex'].pop(site.name)
        self.props['participants'].remove(s)

        pop = site.props['pop']
        hwSwitch = pop.props['hwSwitch']
        port = hwSwitch.props['sitePortIndex'][site.name]
        self.props['siteIndex'].pop("%s.%d" % (port.name, siteVlan))
        return True

    def addHost(self, host):
        # could be invoked in CLI
        if not 'site' in host.props:
            # this might be a serviceVm?
            return False
        site = host.props['site']
        if not site.name in self.props['participantIndex']:
            return False
        self.props['participantIndex'][site.name][1].append(host)
        return True

    def delHost(self, host):
        # could be invoked in CLI
        if not 'site' in host.props:
            # this might be a serviceVm?
            return False
        site = host.props['site']
        if not site.name in self.props['participantIndex']:
            return False
        if not host in self.props['participantIndex'][site.name][1]:
            return False
        self.props['participantIndex'][site.name][1].remove(host)
        return True

class Site(Properties):
    def __init__(self, name, props={}):
        super(Site, self).__init__(name)
        siteRouter = SiteRouter(name)
        self.props['siteRouter'] = siteRouter
        # configure when connecting a Host
        self.props['hosts'] = []
        self.props['links'] = [] # Link fr SiteRouter to Host & BorderRouter
        # configure when connecting to a Pop
        self.props['borderRouter'] = None # CoreRouter
        self.props['pop'] = None # SDNPop
        self.update(props)
    def addHost(self, host):
        self.props['hosts'].append(host)
        siteRouter = self.props['siteRouter']
        link = Link.create(siteRouter, host)
        link.setPortType('SiteToHost', 'HostToSite')
        host.setSite(self)
        siteRouter.addHost(host, link)
        self.props['links'].append(link)
    def setPop(self, pop, link):
        self.props['pop'] = pop
        self.props['borderRouter'] = pop.props['coreRouter']
        self.props['siteRouter'].setWanLink(link)
        self.props['links'].append(link)
class Wan(Properties):
    def __init__(self, name, props={}):
        super(Wan, self).__init__(name)
        self.props['pops'] = []
        self.props['links'] = [] # links between pops and their stitched link to hwSwitch
        self.update(props)
    def connectAll(self, pops, initVlan):
        vlanIndex = initVlan
        for i in range(len(pops)):
            pop1 = pops[i]
            for j in range(i+1, len(pops)):
                pop2 = pops[j]
                self.connect(pop1, pop2, vlanIndex)
                vlanIndex += 1
        self.props['pops'].extend(pops)
    def connect(self, pop1, pop2, vlan):
        # pop[wan_port] --wanlink -- [wan_port]pop
        coreRouter1 = pop1.props['coreRouter']
        coreRouter2 = pop2.props['coreRouter']
        wanlink = Link.create(coreRouter1, coreRouter2, vlan)
        wanlink.setPortType('CoreToCore.WAN', 'CoreToCore.WAN')
        self.props['links'].append(wanlink)

        (hwlink1, swlink1) = pop1.connectPop(pop2, wanlink, vlan)
        self.props['links'].extend([hwlink1, swlink1])
        (hwlink2, swlink2) = pop2.connectPop(pop1, wanlink, vlan)
        self.props['links'].extend([hwlink2, swlink2])
    def subsetLinks(self, pops):
        # return all links that connecting pops including the stitched links to hwSwitch
        links = []
        for i in range(len(pops)):
            pop1 = pops[i]
            coreRouter1 = pop1.props['coreRouter']
            for j in range(i+1, len(pops)):
                pop2 = pops[j]
                coreRouter2 = pop2.props['coreRouter']
                port1 = coreRouter1.props['wanPortIndex'][pop2.name]
                links.append(port1.props['links'][0])
                links.append(coreRouter1.props['stitchedPortIndex.WAN'][port1.name].props['links'][0])
                port2 = coreRouter2.props['wanPortIndex'][pop1.name]
                links.append(coreRouter2.props['stitchedPortIndex.WAN'][port2.name].props['links'][0])
        return links
class Link(Properties):
    def __init__(self, name, props={}):
        super(Link, self).__init__(name)
        self.props['endpoints'] = [] # [Port, Port]
        self.props['portIndex'] = {} # [nodename] = Port
        self.props['vlan'] = 0
        self.update(props)
    @staticmethod
    def create(node1, node2, vlan=0, interfaceIndex1=0, interfaceIndex2=0):
        port1 = node1.getPort(interfaceIndex1)
        port2 = node2.getPort(interfaceIndex2)
        link = Link(name='%s:%s' % (port1.name, port2.name))
        link.props['endpoints'] = [port1, port2]
        link.props['portIndex'] = {node1.name:port1, node2.name:port2}
        link.props['vlan'] = vlan
        if vlan:
            port1.props['vlan'] = vlan
            port2.props['vlan'] = vlan
        port1.props['links'].append(link)
        port2.props['links'].append(link)
        return link
    def setPortType(self, type1, type2):
        self.props['endpoints'][0].props['type'] = type1
        self.props['endpoints'][1].props['type'] = type2
    def __repr__(self):
        return '%s.%r' % (self.name, self.props['vlan'])
