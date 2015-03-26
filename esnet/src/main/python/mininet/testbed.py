#!/usr/bin/python
#
# Default VPN instances
# Each VPN instance is made of an array containing its name and an array of sites
# Each site  is an array of [hostnames,border router, VLAN] where hostnames is
# an array of hostnames of the site.
#

from api import  Node, SDNPop,Link,Port,Site,VPN

vpn1=["vpn1",[
    ["lbl.gov",["dtn-1","dtn-2"],"lbl",1,11],
    ["anl.gov",["dtn-1"],"star",1,12]
  ]
]

vpns=[vpn1]
# Default Locations with hardware openflow switch
# name,rt,nb of links
#
lbl=["lbl",'lbl-tb-of-1',"lbl-mr2",2]
atla=["atla",'atla-tb-of-1',"atla-cr5",4]
denv=["denv",'denv-tb-of-1',"denv-cr5",2]
wash=["wash",'wash-tb-of-1',"wash-cr5",2]
aofa=["aofa",'aofa-tb-of-1',"aofa-cr5",2]
star=["star",'star-tb-of-4',"star-cr5",8]
cern=["cern",'cern-tb-of-1',"cern-cr5",5]
amst=["amst",'amst-tb-of-1',"amst-cr5",8]

# Default locations
locations=[atla,lbl,denv,wash,aofa,star,cern,amst]

class TopoBuilder ():

    def __init__(self, fileName = None,network={'ip':'192.168.1.','netmask':'/24'}):
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
        self.dpidToName = {}
        self.mininetToRealNames = {}

        if fileName != None:
            self.loadConfiguration(fileName)
        else:
            self.locations = [atla,lbl,denv,wash,aofa,star,cern,amst]
            self.vpnInstances = [vpn1]
        self.loadDefault()

    def createLink(self,endpoints,suffix=""):
        link = Link(name=endpoints[0].name+":"+endpoints[1].name+suffix)
        port1 = endpoints[0].newPort({'link':link.name})
        port2 = endpoints[1].newPort({'link':link.name})
        link.props['endpoints'].append(port1)
        link.props['endpoints'].append(port2)
        return link


    def loadDefault(self):

        for location in self.locations:

            name = location[0]
            pop = SDNPop(name)
            hwSwitch = Node(name=location[1],props=self.getSwitchParams(location[1]),builder=self)
            pop.props['hwSwitch'] = hwSwitch
            self.hwSwitches[hwSwitch.name] = hwSwitch
            coreRouter = Node(name=location[2],props=self.getSwitchParams(location[2]),builder=self)
            pop.props['coreRouter'] = coreRouter
            self.coreRouters[coreRouter.name] = coreRouter
            pop.props['nbOfLinks'] = nbOfLinks = location[3]
            switchName = location[0] + "-" "ovs"
            swSwitch = Node(name=switchName, props=self.getSwitchParams(switchName),builder=self)
            pop.props['swSwitch'] = swSwitch
            self.swSwitches[swSwitch.name] = swSwitch

            while (nbOfLinks > 0):
                # create links between the core router and the hardware SDN switch
                link = self.createLink(endpoints=[hwSwitch,coreRouter],suffix=str(nbOfLinks))
                self.coreLinks[link.name] = link
                # create links between the sotfware SDN switch and the hardware SDN switch
                link = self.createLink(endpoints=[hwSwitch,swSwitch],suffix='-' + str(nbOfLinks))
                self.coreLinks[link.name] = link
                nbOfLinks -= 1

            self.pops[name] = pop

        # create mesh between core routers
        # two links are created between any core router, each of them with a different QoS (TBD)
        # one best effort no cap, the other bandwidth limited to low.
        targets = self.coreRouters.items()
        for fromNode in self.coreRouters.items():
            targets = targets[1:]
            for toNode in targets:
                link = self.createLink(endpoints=[fromNode[1],toNode[1]],suffix=":best-effort")
                self.coreLinks[link.name] = link
                link = self.createLink(endpoints=[fromNode[1],toNode[1]],suffix=":slow")
                self.coreLinks[link.name] = link

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
                site.props['connectedTo'] = coreRouter.name
                for h in s[1]:
                    name = h + "@" + site.name
                    host = Node (name=name, props=self.getHostParams(name=h),builder=self)
                    host.props['vlan'] = s[4]
                    site.props['hosts'][host.name] = host
                    link = self.createLink(endpoints=[siteRouter,host],suffix="-" + vpn.name)
                    site.props['links'][link.name] = link

                site.props['vlan'] = s[4]
                # Creates service vm
                name = v[0] + "-" + s[2] + "-vm"
                host = Node(name=name, props=self.getHostParams(name = name),builder=self)
                host.props['vlan'] = s[3]
                if not site.props.has_key('serviceVm'):
                    site.props['serviceVm'] = host
                    link = self.createLink(endpoints=[coreRouter,host],suffix="-" + vpn.name)
                    site.props['links'][link.name] = link
                link = self.createLink(endpoints=[siteRouter,coreRouter],suffix="-" + vpn.name)
                serviceVm = site.props['serviceVm']
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
        dpid = str(index)
        self.dpidToName[dpid] = name
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
    vpns = topo.vpns

	
