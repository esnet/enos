#!/usr/bin/python
#
# Default VPN instances
# Each VPN instance is made of an array containing its name and an array of sites
# Each site  is an array of [hostnames,border router, VLAN] where hostnames is
# an array of hostnames of the site.
#
import struct,binascii
from array import array

from common.api import  Node, SDNPop, Link, Port, Site, VPN
from common.openflow import OpenFlowSwitch

vpn1=["vpn1",[
    ["lbl.gov",["dtn-1","dtn-2"],"lbl",10,11],
    ["anl.gov",["dtn-1"],"star",10,12],
    ["cern.ch",["dtn-1"],"cern",10,13]
  ]
]

vpns=[vpn1]
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
        self.hostIndex = 1
        self.switchIndex = 1
        self.dpidIndex = 1
        self.nodes = {}
        self.pops = {}
        self.coreLinks = {}
        self.coreRouters = {}
        self.hwSwitches = {}
        self.swSwitches = {}
        self.vpns = {}
        self.network = network
        if self.network['ip'][-1] == '.':
            self.network['ip'] = self.network['ip'][:-1]
        self.dpidToName = {}
        self.mininetToRealNames = {}
        self.controller = controller

        if fileName != None:
            self.loadConfiguration(fileName)
        else:
            self.locations = [atla,lbl,denv,wash,aofa,star,cern,amst]
            self.vpnInstances = [vpn1]
        self.loadDefault()

    def displaySwitches(self):
        print "\nName\t\t\tDPID\t\tODL Name\tMininet Name\n"
        for (x,sw) in self.nodes.items():
            if 'dpid' in sw.props:
                print sw.name,"\t",binascii.hexlify(sw.props['dpid']),"\topenflow:" + str(sw.props['dpid'][7]),"\t",sw.props['mininetName']
        print "\n\n"

    def createLink(self,endpoints,vlan,suffix=""):
        link = Link(name=endpoints[0].name+":"+endpoints[1].name+suffix)
        port1 = endpoints[0].newPort({'link':link.name})
        port2 = endpoints[1].newPort({'link':link.name})
        link.props['endpoints'].append(port1)
        link.props['endpoints'].append(port2)
        if vlan:
            link.props['vlan'] = vlan
        return link


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

            name = location[0]
            pop = SDNPop(name)
            # dpid, controller
            swprops = self.getSwitchParams(location[1])
            hwSwitch = OpenFlowSwitch(name = location[1], dpid = swprops['dpid'], controller = self.controller, props = swprops, builder = self)
            pop.props['hwSwitch'] = hwSwitch
            hwSwitch.props['role'] = "HwSwitch"
            hwSwitch.props['pop'] = pop
            self.hwSwitches[hwSwitch.name] = hwSwitch
            # dpid, controller
            swprops = self.getSwitchParams(location[2])
            coreRouter = OpenFlowSwitch(name = location[2], dpid = swprops['dpid'], controller = self.controller, props = swprops, builder = self)
            pop.props['coreRouter'] = coreRouter
            coreRouter.props['role'] = "CoreRouter"
            coreRouter.props['pop'] = pop
            coreRouter.props['WAN-Circuits'] = []
            self.coreRouters[coreRouter.name] = coreRouter
            pop.props['nbOfLinks'] = nbOfLinks = location[3]
            switchName = location[0] + "-" "ovs"
            # dpid, controller
            swprops = self.getSwitchParams(switchName)
            swSwitch = OpenFlowSwitch(name = switchName, dpid = swprops['dpid'], controller = self.controller, props = swprops, builder = self)
            pop.props['swSwitch'] = swSwitch
            swSwitch.props['role'] = "SwSwitch"
            swSwitch.props['pop'] = pop
            self.swSwitches[swSwitch.name] = swSwitch

            links1 = []
            links2 = []
            while (nbOfLinks > 0):
                # create links between the core router and the hardware SDN switch
                link = self.createLink(endpoints=[hwSwitch,coreRouter],vlan=nbOfLinks,suffix=str(nbOfLinks))
                self.coreLinks[link.name] = link
                links1.append(link)
                # create links between the software SDN switch and the hardware SDN switch
                link = self.createLink(endpoints=[hwSwitch,swSwitch],vlan=nbOfLinks,suffix='-' + str(nbOfLinks))
                self.coreLinks[link.name] = link
                links2.append(link)
                nbOfLinks -= 1
            coreRouter.props['toHwSwitch'] = links1
            hwSwitch.props['toCoreRouter'] = links1
            hwSwitch.props['toSwSwitch'] = links2
            swSwitch.props['toHwSwitch'] = links2
            self.pops[name] = pop

        # create mesh between core routers, attached to VLANs between the core routers and hardware switches
        targets = self.coreRouters.items()
        vlanIndex = 1000

        for (x,fromNode) in self.coreRouters.items():
            targets = targets[1:]
            for (z,toNode) in targets:
                link = self.createLink(endpoints=[fromNode,toNode],vlan=vlanIndex)
                self.coreLinks[link.name] = link
                toNode.props['WAN-Circuits'].append(link)
                fromNode.props['WAN-Circuits'].append(link)

                if self.debug:
                    print "To:  " + fromNode.name + " -> " + toNode.name

                toHwSwitch = toNode.props['pop'].props['hwSwitch']
                link2 = self.createLink(endpoints=[toNode,toHwSwitch], vlan=vlanIndex, suffix='-vlan'+str(vlanIndex))
                # Automatically updates toHwSwitch.props['toCoreRouter']
                toNode.props['toHwSwitch'].append(link2)
                self.coreLinks[link2.name] = link2
                if self.debug:
                    print "link2 " + str(link2)

                fromHwSwitch = fromNode.props['pop'].props['hwSwitch']
                link3 = self.createLink(endpoints=[fromNode,fromHwSwitch], vlan=vlanIndex, suffix='-vlan'+str(vlanIndex))
                # Automatically updates fromHwSwitch.props['toCoreRouter']
                fromNode.props['toHwSwitch'].append(link3)
                self.coreLinks[link3.name] = link3
                if self.debug:
                    print "link3 " + str(link3)

                vlanIndex += 1

        for v in self.vpnInstances:
            vpn = VPN (v[0])
            self.vpns[vpn.name] = vpn
            for s in v[1]:
                site = Site(s[0])
                vpn.props['sites'][site.name] = site
                name = s[0]
                siteRouter = Node(name=name, props = self.getSwitchParams(name=name),builder=self)
                site.props['siteRouter'] = siteRouter
                pop = self.pops[s[2]]
                coreRouter = pop.props['coreRouter']
                swSwitch = pop.props['swSwitch']
                site.props['connectedTo'] = coreRouter.name
                vlan = s[3]
                for h in s[1]:
                    name = h + "@" + site.name
                    host = Node (name=name, props=self.getHostParams(name=h),builder=self)
                    host.props['vlan'] = vlan
                    site.props['hosts'][host.name] = host
                    link = self.createLink(endpoints=[siteRouter,host],suffix="-" + vpn.name,vlan=vlan)
                    site.props['links'][link.name] = link

                site.props['vlan'] = vlan
                if not site.props.has_key('serviceVm'):
                    # Creates service vm
                    name = v[0] + "-" + s[2] + "-vm"
                    host = Node(name=name, props=self.getHostParams(name = name),builder=self)
                    vlan = s[4]
                    host.props['vlan'] = vlan
                    host.props['role'] = "ServiceVm"
                    site.props['serviceVm'] = host
                    link = self.createLink(endpoints=[swSwitch,host],vlan=host.props['vlan'],suffix="-" + vpn.name)
                    site.props['links'][link.name] = link
                link = self.createLink(endpoints=[siteRouter,coreRouter],vlan=host.props['vlan'],suffix="-" + vpn.name)
                site.props['links'][link.name] = link

            self.vpns [vpn.name] = vpn


    def getHostParams(self,name):
        index = self.hostIndex
        self.hostIndex +=  1
        mininetName = "h" + str(index)
        self.mininetToRealNames[mininetName] = name
        ip = self.network['ip'] + "." + str(index) + self.network['netmask']
        return {'mininetName' : mininetName, 'ip' : ip}

    def getSwitchParams(self,name):
        index = self.switchIndex
        self.switchIndex += 1
        mininetName = "s" + str(index)
        self.mininetToRealNames[mininetName] = name
        # Create dpid
        index = self.dpidIndex
        self.dpidIndex = self.dpidIndex + 1
        dpid = array('B',struct.unpack("8B", struct.pack("!Q", index)))
        self.dpidToName[str(dpid)] = name
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

	
