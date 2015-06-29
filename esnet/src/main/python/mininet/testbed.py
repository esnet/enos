#!/usr/bin/python
#
# Default VPN instances
# Each VPN instance is made of an array containing its name and an array of sites
# Each site  is an array of [hostnames,border router, VLAN] where hostnames is
# an array of hostnames of the site.
#
import struct,binascii
from array import array

from common.api import Node, SDNPop, Link, Port, Site, VPN, Host, ServiceVm, SiteRouter, CoreRouter, HwSwitch, SwSwitch
from common.mac import MACAddress

# All switches including site routers, core routers, hw switches, and sw switches should
# not have the same name so that the name of each port could be unique.
lblsite = ["lbl.gov",['dtn-1', 'dtn-2'],"lbl"]
anlsite = ["anl.gov",['dtn-1', 'dtn-2'],"star"]
cernsite = ["cern.ch",['dtn-1', 'dtn-2'],"cern"]
sites = [lblsite, anlsite, cernsite]
vpn1=["vpn1", 1234, 10, [
    ("lbl.gov", ['dtn-1', 'dtn-2'], 11), 
    ("anl.gov", ['dtn-1', 'dtn-2'], 12),
    ("cern.ch", ['dtn-1', 'dtn-2'], 13)
    ]
]
vpn2=["vpn2", 5678, 20, [
    ("lbl.gov", ['dtn-1'], 21),
    ("anl.gov", ['dtn-1'], 22)
    ]
]
vpns=[vpn1, vpn2]
# Default Locations with hardware openflow switch
# name,rt,nb of links
#
#lbl=["lbl",'lbl-tb-of-1',"lbl-mr2",2]
#atla=["atla",'atla-tb-of-1',"atla-cr5",4]
#denv=["denv",'denv-tb-of-1',"denv-cr5",2]
#wash=["wash",'wash-tb-of-1',"wash-cr5",2]
#aofa=["aofa",'aofa-tb-of-1',"aofa-cr5",2]
#star=["star",'star-tb-of-4',"star-cr5",8]
#cern=["cern",'cern-tb-of-1',"cern-cr5",5]
#amst=["amst",'amst-tb-of-1',"amst-cr5",8]

lbl=["lbl",'lbl-tb-of-1',"lbl-mr2",1]
atla=["atla",'atla-tb-of-1',"atla-cr5",1]
denv=["denv",'denv-tb-of-1',"denv-cr5",1]
wash=["wash",'wash-tb-of-1',"wash-cr5",1]
aofa=["aofa",'aofa-tb-of-1',"aofa-cr5",1]
star=["star",'star-tb-of-4',"star-cr5",1]
cern=["cern",'cern-tb-of-1',"cern-cr5",1]
amst=["amst",'amst-tb-of-1',"amst-cr5",1]

# Default locations
locations=[atla,lbl,denv,wash,aofa,star,cern,amst]
class TopoBuilder ():

    debug = False;

    def __init__(self, fileName = None, network={'ip':'192.168.1.','netmask':'/24'}, controller = None):
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
        self.nodes = {}
        self.hosts = []
        self.hostIndex = {} # [hostname] = Host
        self.switches = []
        self.links = []
        self.sites = []
        self.siteIndex = {} # [sitename] = Site
        self.sitesConfig = []
        self.pops = []
        self.popIndex = {} # [popname] = SDNPop
        self.vpns = []
        self.network = network
        if self.network['ip'][-1] == '.':
            self.network['ip'] = self.network['ip'][:-1]
        self.dpidToName = {}
        self.mininetToRealNames = {}
        self.controller = controller

        if fileName != None:
            self.loadConfiguration(fileName)
        else:
            self.locations = locations
            self.sitesConfig = sites
            self.vpnInstances = vpns
        self.loadDefault()

    def displaySwitches(self):
        print "\nName\t\t\tDPID\t\tODL Name\tMininet Name\n"
        for sw in self.switches:
            if 'dpid' in sw.props:
                print sw.name,"\t",binascii.hexlify(sw.props['dpid']),"\topenflow:" + str(sw.props['dpid'][7]),"\t",sw.props['mininetName']
        print "\n\n"

    def displayHosts(self,vpn):
        print "\nName\t\tIPv4 Address\tVLAN\tMininet Name\t"
        for host in self.hosts:
            print h.name,"\t",h.props['ip'],"\t",vpn.props['lanVlan'],"\t",h.props['mininetName']
        print "\n\n"

    def addSwitch(self, name):
        switch = Switch(name=name)
        self.switches.append(switch)
        return switch

    def addSDNPop(self, popname, hwswitchname, coreroutername, swswitchname, nbOfLinks):
        pop = SDNPop(popname, hwswitchname, coreroutername, swswitchname, nbOfLinks)
        hwSwitch = pop.props['hwSwitch']
        coreRouter = pop.props['coreRouter']
        swSwitch = pop.props['swSwitch']
        self.switches.append(hwSwitch)
        self.switches.append(coreRouter)
        self.switches.append(swSwitch)
        for link in hwSwitch.get('toCoreRouter'):
            self.links.append(link)
        for link in hwSwitch.get('toSwSwitch'):
            self.links.append(link)
        return pop

    def connect(self, pop1, pop2, vlan):
        coreRouter1 = pop1.get('coreRouter')
        coreRouter2 = pop2.get('coreRouter')
        hwSwitch1 = pop1.get('hwSwitch')
        hwSwitch2 = pop2.get('hwSwitch')
        link11 = Link.create(coreRouter1, hwSwitch1, vlan)
        link11.setPortType('WANToSDN', 'ToWAN')
        link12 = Link.create(coreRouter1, coreRouter2, vlan)
        link12.setPortType('ToWAN', 'ToWAN')
        link22 = Link.create(coreRouter2, hwSwitch2, vlan)
        link22.setPortType('WANToSDN', 'ToWAN')
        coreRouter1.props['WAN-Circuits'].append(link12)
        coreRouter1.props['toWanPorts'].append(link12.props['endpoints'][0])
        coreRouter2.props['toWanPorts'].append(link12.props['endpoints'][1])
        coreRouter2.props['WAN-Circuits'].append(link12)

        coreRouter1.props['toHwSwitch'].append(link11)
        coreRouter2.props['toHwSwitch'].append(link22)
        coreRouter1.props['toHwSwitchPorts'].append(link11.props['endpoints'][0])
        coreRouter2.props['toHwSwitchPorts'].append(link22.props['endpoints'][0])
        hwSwitch1.props['nextHop'][pop2.name] = link12
        hwSwitch2.props['nextHop'][pop1.name] = link12

        self.links.append(link11)
        self.links.append(link12)
        self.links.append(link22)
    def updateHost(self, host):
        host.update(self.getHostParams(host.name))
    def updateSwitch(self, switch):
        switch.update(self.getSwitchParams(switch.name))
        role = switch.get('role')
        if role: # hwSwitch, coreRouter, swSwitch
            switch.update({'controller':self.controller})
    def loadDefault(self):
        """
            We make several simplifying assumptions here:
            1.  All POPs have roughly the same "shape", with a hardware switch, a software switch,
                and a core router.
            2.  The router is simulated by an OpenFlow switch.
            3.  All OpenFlow switches have the same controller object used to access them.
            4.  All OpenFlow switches can be represented by the same object class.
        """
        for location in self.locations:
            (popname, hwswitchname, coreroutername, swswitchname, nbOfLinks) = (location[0], location[1], location[2], location[0] + "-ovs", location[3])
            pop = self.addSDNPop(popname, hwswitchname, coreroutername, swswitchname, nbOfLinks)
            self.popIndex[popname] = pop
            self.pops.append(pop)

        # create mesh between core routers, attached to VLANs between the core routers and hardware switches
        pops = self.pops
        vlanIndex = 1000
        for i in range(len(pops)):
            pop1 = pops[i]
            for j in range(i+1, len(pops)):
                pop2 = pops[j]
                self.connect(pop1, pop2, vlanIndex)
                vlanIndex += 1

        # might be skip if vpn's information is complete
        for (sitename, hostnames, popname) in self.sitesConfig:
            site = self.addSite(sitename, popname)
            # TODO lanVlan wanVlan
            for name in hostnames:
                hostname = name + "@" + sitename
                host = self.addHost(hostname)
                site.addHost(host)
            self.links.extend(site.get('links'))

        for (vpnname, vid, lanVlan, participants) in self.vpnInstances:
            vpn = VPN(vpnname, vid, lanVlan)
            for (sitename, hostnames, wanVlan) in participants:
                site = self.siteIndex[sitename]
                hosts = map(lambda hostname : self.hostIndex['%s@%s' % (hostname, sitename)], hostnames)
                vpn.addParticipant(site, hosts, wanVlan)
            self.hosts.extend(vpn.props['serviceVms'])
            self.links.extend(vpn.props['serviceVmLinks'])
            self.vpns.append(vpn)
        for host in self.hosts:
            self.updateHost(host)
        for switch in self.switches:
            self.updateSwitch(switch)
    def addSite(self, sitename, popname):
        site = Site(sitename)
        siteRouter = site.get('siteRouter')
        self.switches.append(siteRouter)
        pop = self.popIndex[popname]
        site.props['pop'] = pop
        coreRouter = pop.get('coreRouter')
        site.props['borderRouter'] = coreRouter

        link = Link.create(siteRouter, coreRouter)
        link.props['endpoints'][0].props['type'] = 'ToWAN'
        link.props['endpoints'][1].props['type'] = 'ToSite'
        siteRouter.props['toWanPort'] = link.props['endpoints'][0]
        coreRouter.props['toSitePort'] = link.props['endpoints'][1]
        site.props['links'].append(link)
        self.siteIndex[sitename] = site
        self.sites.append(site)
        return site
    def addHost(self, name):
        host = Host(name=name)
        self.hosts.append(host)
        self.hostIndex[host.name] = host
        return host
    def getHostParams(self,name):
        index = self.hostID
        self.hostID +=  1
        mininetName = "h" + str(index)
        self.mininetToRealNames[mininetName] = name
        ip = self.network['ip'] + "." + str(index) + self.network['netmask']
        return {'mininetName' : mininetName, 'ip' : ip, 'mac' : MACAddress(index)}

    def getSwitchParams(self,name):
        index = self.switchID
        self.switchID += 1
        # for mininet
        mininetName = "s" + str(index)
        self.mininetToRealNames[mininetName] = name
        # Create dpid
        index = self.dpidIndex
        self.dpidIndex += 1
        dpid = array('B',struct.unpack("8B", struct.pack("!Q", index)))
        self.dpidToName[binascii.hexlify(dpid)] = name
        return {"mininetName" : mininetName, "dpid" : dpid}


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


	
