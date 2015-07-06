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
        self.props['vlanIndex'] = {} # [vid] = mod_vlan
        self.props['scopeIndex'] = {} # [vid] = Scope
        self.props['vlan'] = 0
        self.update(props)
    def __repr__(self):
        return 'Port(name=%s, interfaceIndex=%d, vlan=%d, vlanIndex=%r' % (self.name, self.props['interfaceIndex'], self.props['vlan'], self.props['vlanIndex'])

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
        super(Host, self).__init__(name, props=props)

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
        super(CoreRouter, self).__init__(name, props=props)
        self.props['role'] = 'CoreRouter'
        self.props['WAN-Circuits'] = [] # list of Link between coreRouters
        self.props['siteToHwSwitch'] = [] # list of Link to hwSwitch (stitch with siteRouter)
        self.props['toHwSwitch'] = [] # list of Link to hwSwitch (stitch with coreRouter)
        self.props['toSitePort'] = None # Port (might be empty if no site)
        self.props['pop'] = None

class HwSwitch(Switch):
    def __init__(self, name, props={}):
        super(HwSwitch, self).__init__(name, props=props)
        self.props['role'] = 'HwSwitch'
        self.props['toCoreRouter'] = [] # list of Link toward site
        self.props['toSwSwitch'] = [] # list of Link to swSwitch
        self.props['nextHop'] = {} # [pop.name] = Link
        self.props['pop'] = None
        self.props['siteVlanIndex'] = {} # [vid] = vlan

class SwSwitch(Switch):
    def __init__(self, name, props={}):
        super(SwSwitch, self).__init__(name, props=props)
        self.props['role'] = 'SwSwitch'
        self.props['toHwSwitch'] = [] # list of Link to hwSwitch
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
            link1 = Link.create(coreRouter, hwSwitch, vlan)
            link1.setPortType('SiteToSDN', 'ToSite')
            coreRouter.props['siteToHwSwitch'].append(link1)
            hwSwitch.props['toCoreRouter'].append(link1)
            link2 = Link.create(hwSwitch, swSwitch, vlan)
            link2.setPortType('ToSwSwitch', 'ToHwSwitch')
            hwSwitch.props['toSwSwitch'].append(link2)
            swSwitch.props['toHwSwitch'].append(link2)
            self.props['links'].append(link1)
            self.props['links'].append(link2)
        self.props['hwSwitch'] = hwSwitch
        self.props['coreRouter'] = coreRouter
        self.props['swSwitch'] = swSwitch
        self.props['nbOfLinks'] = nbOfLinks

class VPN(Properties):
    def __init__(self, name, vid, lanVlan, props={}):
        super(VPN, self).__init__(name, props=props)
        self.props['vid'] = vid
        self.props['lanVlan'] = lanVlan
        self.props['participants'] = [] # list of (site, hosts, wanVlan)
        self.props['serviceVms'] = []
        self.props['serviceVmIndex'] = {} # [sitename] = serviceVm
        self.props['links'] = []
        self.props['mat'] = None # MAC Address Translation
    def addParticipant(self, site, hosts, wanVlan):
        # create a service vm (host) and connect it to sw switch
        pop = site.props['pop']
        serviceVm = ServiceVm('%s-%s-vm' % (self.name, pop.name))
        self.props['serviceVms'].append(serviceVm)
        self.props['serviceVmIndex'][site.name] = serviceVm
        swSwitch = pop.props['swSwitch']
        link = Link.create(serviceVm, swSwitch, wanVlan)
        link.setPortType('ToServiceVm', 'VLAN')
        self.props['links'].append(link)
        self.props['participants'].append((site, hosts, wanVlan))

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
        link.setPortType('ToLAN', 'LAN')
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
        coreRouter1 = pop1.props['coreRouter']
        coreRouter2 = pop2.props['coreRouter']
        link = Link.create(coreRouter1, coreRouter2, vlan)
        link.setPortType('WAN', 'WAN')
        self.props['links'].append(link)
        coreRouter1.props['WAN-Circuits'].append(link)
        coreRouter2.props['WAN-Circuits'].append(link)

        hwSwitch1 = pop1.props['hwSwitch']
        link1 = Link.create(coreRouter1, hwSwitch1, vlan)
        link1.setPortType('WANToSDN', 'ToWAN')
        self.props['links'].append(link1)
        coreRouter1.props['toHwSwitch'].append(link1)
        hwSwitch1.props['nextHop'][pop2.name] = link1

        hwSwitch2 = pop2.props['hwSwitch']
        link2 = Link.create(coreRouter2, hwSwitch2, vlan)
        link2.setPortType('WANToSDN', 'ToWAN')
        self.props['links'].append(link2)
        coreRouter2.props['toHwSwitch'].append(link2)
        hwSwitch2.props['nextHop'][pop1.name] = link2

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
