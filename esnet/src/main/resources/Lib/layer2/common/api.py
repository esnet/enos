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
import threading
import random

from layer2.common.utils import Logger

db = {}

debug = False


class Properties(object):
    def __init__(self, name,props={}):
        self.name = name
        self.props = {}
        self.update(props)

    def update(self, props):
        if len(props) > 0:
            global db
            db['self'] = self
            db['props'] = props
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
    def __init__(self,name,node=None,props={}):
        super(Port, self).__init__(name)
        # configured by Node:
        self.props['node'] = node
        # configured by Link:
        self.props['links'] = [] # list of Link
        # Others
        self.props['vlan'] = 0
        self.update(props)
    def __repr__(self):
        return 'Port(name=%s)' % (self.name)
    def getLink(self,n1,p1,n2,p2,vlan):
        links = self.props['links']
        for link in links:
            endpoints = link.props['endpoints']
            v = link.props['vlan']
            port1 = endpoints[0]
            port2 = endpoints[1]
            node1 = port1.props['node']
            node2 = port2.props['node']
            if (node1.name,port1.name,node2.name,port2.name,v) == (n1,p1,n2,p2,vlan):
                return link
        return None


class Node(Properties):
    def __init__(self, name, domain='es.net',props={}):
        super(Node, self).__init__(name)
        self.props['ports'] = {} # [interfaceIndex] = Port
        self.update(props)
        self.props['domain'] = domain

    def addPort(self,port):
        self.props['ports'][port.name] = port
        port.props['node'] = self

    def orderPorts(self,link):
        endpoints = link.props['endpoints']
        vlan = link.props['vlan']
        port1 = endpoints[0]
        port2 = endpoints[1]
        node1 = port1.props['node']
        node2 = port2.props['node']
        if node1.name == self.name:
            return (port1,port2.vlan)
        if node2.name == self.name:
            return (port2,port1)
        return(None,None)

    def portToRemote(self,port):
        """
        Returns the port of that is connected to one of the endpoints of the node/port if any.
        :param node:
        :param port:
        :return:
        """
        res = {}
        node = port.props['node']
        ports = self.props['ports']
        for p in ports.values():
            links = p.props['links']
            for link in links:
                (myPort,remotePort) = self.orderPorts(link)
                if remotePort and remotePort.name == port.name and remotePort.props['node'].name == node.name:
                    return (myPort,link)


class Host(Node):
    def __init__(self, name, domain=None,props={}):
        if domain != None:
            super(Host, self).__init__(name,domain=domain,props=props)
        else:
            super(Host, self).__init__(name,props=props)
        self.props['site'] = None # Site
        self.props.update(props)
    def setSite(self, site):
        self.props['site'] = site

class Switch(Node):
    def __init__(self, name, domain=None,props={}):
        if domain != None:
            super(Switch, self).__init__(name,domain=domain,props=props)
        else:
            super(Switch, self).__init__(name,props=props)


class HwSwitch(Switch):
    logger = Logger('HwSwitch')
    def __init__(self, name, domain=None, props={}):
        if domain != None:
            super(HwSwitch, self).__init__(name,domain=domain,props=props)
        else:
            super(HwSwitch, self).__init__(name,props=props)
        self.props['role'] = 'HwSwitch'
        self.props['pop'] = None

class SwSwitch(Switch):
    logger = Logger('SwSwitch')
    def __init__(self, name, domain=None, props={}):
        if domain != None:
            super(SwSwitch, self).__init__(name,domain=domain,props=props)
        else:
            super(SwSwitch, self).__init__(name,props=props)
        self.props['role'] = 'SwSwitch'
        self.props['pop'] = None

class CoreRouter(Switch):
    def __init__(self, name, domain=None, props={}):
        if domain != None:
            super(CoreRouter, self).__init__(name,domain=domain,props=props)
        else:
            super(CoreRouter, self).__init__(name,props=props)
        self.props['role'] = 'CoreRouter'
        self.props['pop'] = None
        self.props.update(props)


class Link(Properties):
    def __init__(self, ports, vlan=0,props={}):
        name = "#".join([ports[0].props['node'].name,ports[0].name,ports[1].props['node'].name,ports[1].name,str(vlan)])
        super(Link, self).__init__(name)
        self.update(props)
        self.props['portIndex'] = {} # [nodename] = Port
        self.props['vlan'] = 0
        self.props['endpoints'] = ports
        for port in ports:
            self.props['portIndex'] [port.props['node'].name] = port
            if vlan:
                port.props['vlan'] = vlan
        port.props['links'].append(self)
        self.props['vlan'] = vlan

    def __repr__(self):
        return '%s.%r' % (self.name, self.props['vlan'])

class SDNPop(Properties):
    logger = Logger('SDNPop')
    def __init__(self, name, hwswitchname, coreroutername, swswitchname, props={}):
        super(SDNPop, self).__init__(name, props=props)
        self.props['sites'] = []
        hwSwitch = HwSwitch(hwswitchname)
        hwSwitch.props['pop'] = self
        swSwitch = SwSwitch(swswitchname)
        swSwitch.props['pop'] = self
        coreRouter = CoreRouter(coreroutername)
        coreRouter.props['pop'] = self

        self.props['hwSwitch'] = hwSwitch
        self.props['swSwitch'] = swSwitch
        self.props['coreRouter'] = coreRouter

    def addSite(self, site, links):
        if len(links) != 1:
            # This implementation only supports one link between a site and a core router.
            SDNPop.logger.error("Only support one link between %s and network. Found %d" % (site.name,len(links)))
            return

        wanlink = links.values()[0] # Link where VC from site lands
        wanlinkeps = wanlink.props['endpoints']
        wanportName = None # switch port on the hw switch, need to find this
        # Iterate over core-facing ports to find the port where the site circuit lands
        for portName in self.props['hwSwitch'].props['toCorePorts']:
            ls = self.props['hwSwitch'].props['ports'][portName].props['links']
            for link in ls:
                if debug:
                    print "  link " + link.name
                linkeps = link.props['endpoints']
                if linkeps[0] == wanlinkeps[0] or linkeps[0] == wanlinkeps[1] or linkeps[1] == wanlinkeps[0] or linkeps[1] == wanlinkeps[1]:
                    wanportName = portName # found hardware switch port facing the site (circuit)
                    break

        # Iterate over all of the links terminating on that port to find the one that
        # goes to the sw switch.  Presumably there is only one.
        swlink = None
        swport = None

        self.props['hwSwitch'].addSite(site,wanlink)
        self.props['swSwitch'].addSite(site,swlink)
        self.props['sites'].append(site)

        if debug:
            print "SDNPop.addSite completing with site " + site.name + " wanlink " + wanlink.name + " swlink " + swlink.name

class Site(Properties):
    def __init__(self, name, props={}):
        super(Site, self).__init__(name)
        # configure when connecting a Host
        self.props['hosts'] = []
        self.props['links'] = [] # Link fr SiteRouter to Host & BorderRouter
        self.props['pop'] = None # SDNPop
        self.props['switch'] = None
        self.update(props)
    def addSwitch(self,switch):
        self.props['switch'] = switch
    def addHost(self, host,link):
        self.props['hosts'].append(host)
        host.props['link'] = link
        self.props['links'].append(link)
        host.setSite(self)
    def setPop(self, pop):
        self.props['pop'] = pop

class Wan(Properties):
    def __init__(self, name, topo,props={}):
        super(Wan, self).__init__(name)
        self.props['pops'] = []
        self.props['links'] = [] # links between pops and their stitched link to hwSwitch
        self.update(props)
        self.topo = topo

