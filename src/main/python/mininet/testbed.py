#!/usr/bin/python
#
# Default VPN instances
# Each VPN instance is made of an array containing its name and an array of sites
# Each site  is an array of [hostnames,border router, VLAN] where hostnames is
# an array of hostnames of the site.
#

vpn1=["vpn1",[
    ["site1",["site1-host-1","site1-host-2"],"lbl",1,11],
    ["site2",["site2-host-3"],"denv",1,12]
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

    def __init__(self, fileName = None):
        self.hostIndex = 1
        self.switchIndex = 1
        self.dpidIndex = 1
        self.dpidToMininetName = {}
        self.mininetToDpid = {}
        self.realNameToMininetName = {}
        self.mininetNameToRealName = {}
        if fileName != None:
            self.loadConfiguration(fileName)
        else:
            self.locations = [atla,lbl,denv,wash,aofa,star,cern,amst]
            self.vpns = vpns=[vpn1]
            self.loadDefault()

    def loadDefault(self):
        format={}
        locs =[]

        for location in self.locations:
            loc = {}
            loc['name'] = location[0]
            loc["hwSwitch"] = self.makeMininetSwitch(location[1])
            mininetSwitch = self.makeMininetSwitch(location[2])
            loc['coreRouter'] = self.makeMininetSwitch(location[2])
            loc['nbOfLinks'] = location[3]
            # Creates the OVS switch
            switchName = location[0] + "-" "ovs"
            loc['swSwitch'] = self.makeMininetSwitch(switchName)
            locs = locs +[loc]

        instances = []
        network = "192.168"
        networkIndex = 1
        for vpn in self.vpns:
            sites=[]
            instance = {}
            instance['name'] = vpn[0]
            for s in vpn[1]:
                site = {}
                site['name'] = s[0]
                hosts = []
                for h in s[1]:
                    host={}
                    net = network + "." + str(networkIndex)
                    mininetHost = self.makeMininetHost(realName=h[0],network=net)
                    host= self.makeMininetHost(realName=h[0],network=net)
                    host['vlan'] = s[4]
                    hosts = hosts + [host]
                site['hosts'] = hosts
                site['vlan'] = s[4]
                # Create border router
                siteRouterName = s[0] + "-" + s[2] + "-site"
                switch  = self.makeMininetSwitch(realName=siteRouterName)
                site['siteRouter'] = switch
                site['connectedTo'] = s[2]
                # Creates service vm
                host={}
                net = network + "." + str(networkIndex+1)
                host = self.makeMininetHost(realName = s[0] + "-" + s[2] + "-vm", network = net)
                host['vlan'] = s[3]
                site['serviceVm'] = host
                sites = sites + [site]
                networkIndex = networkIndex + 2
            instance['sites'] = sites
            instances = instances + [instance]

        format['topology'] = locs
        format['vpns'] = instances

        self.config = format


    def makeMininetHost(self,realName, network="192.168.1"):
        index = self.hostIndex
        self.hostIndex = self.hostIndex + 1

        mininetName = "h" + str(index)

        self.realNameToMininetName[realName] = mininetName
        self.mininetNameToRealName[mininetName] = realName
        ip = network + "." + str(index)
        return {'name' : mininetName, 'ip' : ip}

    def makeMininetSwitch(self,realName):
        index = self.switchIndex
        self.switchIndex = self.switchIndex + 1

        mininetName = "s" + str(index)

        self.realNameToMininetName[realName] = mininetName
        self.mininetNameToRealName[mininetName] = realName

        # Create dpid
        index = self.dpidIndex
        self.dpidIndex = self.dpidIndex + 1
        dpid = str(index)
        self.dpidToMininetName[dpid] = realName
        self.mininetToDpid[realName] = dpid

        return {"name" : mininetName, "dpid" : dpid}


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
    print topo.config
	
