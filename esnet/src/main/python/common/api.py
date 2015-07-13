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
        self.props['connectTo'] = None # a SiteRouter (or a SwSwitch if self is ServiceVm)
        self.props.update(props)

class ServiceVm(Host):
    def __init__(self, name, props={}):
        super(ServiceVm, self).__init__(name)
        self.props['role'] = 'ServiceVm'
        self.props['vlan'] = 0
        self.update(props)

class Switch(Node):
    def __init__(self, name, props={}):
        super(Switch, self).__init__(name, props=props)

class SiteRouter(Switch):
    def __init__(self, name, props={}):
        super(SiteRouter, self).__init__(name, props=props)
        self.props['role'] = 'SiteRouter'
        self.props['toWanPort'] = None # Port

class CoreRouter(Switch):
    def __init__(self, name, props={}):
        super(CoreRouter, self).__init__(name)
        self.props['role'] = 'CoreRouter'
        self.props['WAN-Circuits'] = [] # list of Link between coreRouters
        self.props['pop'] = None
        self.props['toHwPorts'] = [] # nbOfLinks 'CoreToHw' ports
        self.props['stitchedSitePortIndex'] = {} # [tosite_port.name] = stitched port (to hw)
        self.props['stitchedWanPortIndex'] = {} # [portname] = stitched port (WAN) (2 ways)
        self.props['sitePortIndex'] = {} # [sitename] = stitched port to hw
        self.props.update(props)
class HwSwitch(Switch):
    def __init__(self, name, props={}):
        super(HwSwitch, self).__init__(name, props=props)
        self.props['role'] = 'HwSwitch'
        self.props['toCoreRouter'] = [] # list of Link toward site
        self.props['toSwSwitchPort'] = None
        self.props['toSwSwitchPort.WAN'] = None
        self.props['nextHop'] = {} # [pop.name] = Link
        self.props['pop'] = None
        self.props['siteVlanIndex'] = {} # [vid] = vlan
        self.props['sitePortIndex'] = {} # [sitename] = stitched port to core

class SwSwitch(Switch):
    def __init__(self, name, props={}):
        super(SwSwitch, self).__init__(name, props=props)
        self.props['role'] = 'SwSwitch'
        self.props['toHwSwitchPort'] = None
        self.props['toHwSwitchPort.WAN'] = None
        self.props['pop'] = None

class SDNPop(Properties):
    def __init__(self, name, hwswitchname, coreroutername, swswitchname, nbOfLinks=1, props={}):
        super(SDNPop, self).__init__(name, props=props)
        self.props['links'] = []
        hwSwitch = HwSwitch(hwswitchname)
        hwSwitch.props['pop'] = self
        coreRouter = CoreRouter(coreroutername)
        coreRouter.props['pop'] = self
        swSwitch = SwSwitch(swswitchname)
        swSwitch.props['pop'] = self
        for i in range(nbOfLinks):
            vlan = i + 1
            link = Link.create(coreRouter, hwSwitch, vlan)
            link.setPortType('CoreToHw', 'HwToCore')
            port = link.props['portIndex'][coreRouter.name]
            coreRouter.props['toHwPorts'].append(port)
            hwSwitch.props['toCoreRouter'].append(link)
            self.props['links'].append(link)

        link = Link.create(hwSwitch, swSwitch)
        link.setPortType('HwToSw', 'SwToHw')
        hwSwitch.props['toSwSwitchPort'] = link.props['portIndex'][hwSwitch.name]
        swSwitch.props['toHwSwitchPort'] = link.props['portIndex'][swSwitch.name]
        self.props['links'].append(link)
        link = Link.create(hwSwitch, swSwitch)
        link.setPortType('HwToSw.WAN', 'SwToHw.WAN')
        hwSwitch.props['toSwSwitchPort.WAN'] = link.props['portIndex'][hwSwitch.name]
        swSwitch.props['toHwSwitchPort.WAN'] = link.props['portIndex'][swSwitch.name]
        self.props['links'].append(link)

        self.props['hwSwitch'] = hwSwitch
        self.props['coreRouter'] = coreRouter
        self.props['swSwitch'] = swSwitch
        self.props['nbOfLinks'] = nbOfLinks
    def connectPop(self, pop, wanPort, vlan):
        # hw[tocore_port] --<hwlink>-- [core_port]core[wanPort] --<wanlink with vlan>-- pop
        coreRouter = self.props['coreRouter']
        hwSwitch = self.props['hwSwitch']
        hwlink = Link.create(coreRouter, hwSwitch, vlan)
        hwlink.setPortType('CoreToHw.WAN', 'HwToCore.WAN')
        core_port = hwlink.props['portIndex'][coreRouter.name]
        tocore_port = hwlink.props['portIndex'][hwSwitch.name]
        hwSwitch.props['nextHop'][pop.name] = hwlink
        coreRouter.props['stitchedWanPortIndex'][wanPort.name] = core_port
        coreRouter.props['stitchedWanPortIndex'][core_port.name] = wanPort
        return hwlink
class VPN(Properties):
    def __init__(self, name, vid, lanVlan, props={}):
        super(VPN, self).__init__(name, props=props)
        self.props['vid'] = vid # int
        self.props['lanVlan'] = lanVlan # int
        self.props['participants'] = [] # list of (site, hosts, wanVlan)
        self.props['participantIndex'] = {} # [sitename] = (site, hosts, wanVlan)
        self.props['serviceVms'] = [] # list of ServiceVm
        self.props['serviceVmIndex'] = {} # [sitename] = ServiceVm
        self.props['links'] = []
        self.props['mat'] = None # MAC Address Translation
        self.props['renderer'] = None # SDNPopsRenderer
    def addParticipant(self, site, hosts, wanVlan):
        # create a service vm (host) and connect it to sw switch
        pop = site.props['pop']
        serviceVm = ServiceVm('%s-%s-vm' % (self.name, pop.name))
        self.props['serviceVms'].append(serviceVm)
        self.props['serviceVmIndex'][site.name] = serviceVm
        swSwitch = pop.props['swSwitch']
        link = Link.create(serviceVm, swSwitch, wanVlan)
        link.setPortType('SwToVm', 'VmToSw')
        self.props['links'].append(link)
        participant = (site, hosts, wanVlan)
        self.props['participants'].append(participant)
        self.props['participantIndex'][site.name] = participant
    def addSite(self, site, wanVlan):
        # could be invoked in CLI
        pop = site.props['pop']
        serviceVm = ServiceVm('%s-%s-vm' % (self.name, pop.name))
        self.props['serviceVms'].append(serviceVm)
        self.props['serviceVmIndex'][site.name] = serviceVm
        swSwitch = pop.props['swSwitch']
        link = Link.create(serviceVm, swSwitch, wanVlan)
        link.setPortType('SwToVm', 'VmToSw')
        serviceVm.props['connectTo'] = swSwitch
        self.props['links'].append(link)
        participant = (site, [], wanVlan)
        self.props['participants'].append(participant)
        self.props['participantIndex'][site.name] = participant
        return (serviceVm, link)
    def addHost(self, host):
        # could be invoked in CLI
        sitename = host.props['connectTo'].name # sitename == siteRouterName
        self.props['participantIndex'][sitename][1].append(host)
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
        host.props['connectTo'] = siteRouter
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
        wan_port1 = wanlink.props['portIndex'][coreRouter1.name]
        wan_port2 = wanlink.props['portIndex'][coreRouter2.name]
        self.props['links'].append(wanlink)
        coreRouter1.props['WAN-Circuits'].append(wanlink)
        coreRouter2.props['WAN-Circuits'].append(wanlink)

        hwlink1 = pop1.connectPop(pop2, wan_port1, vlan)
        self.props['links'].append(hwlink1)
        hwlink2 = pop2.connectPop(pop1, wan_port2, vlan)
        self.props['links'].append(hwlink2)

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
