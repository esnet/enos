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
import binascii
import logging,random
from layer2.common.mac import MACAddress
from layer2.testbed.oscars import getgri,getcoregris,getgrinode
from layer2.testbed.topology import TestbedTopology
from layer2.testbed.builder import tbns
from layer2.vpn.mat import MAT
from layer2.common.utils import mapResource
from net.es.netshell.api import Resource,Container
from net.es.netshell.boot import BootStrap

import sys
if "debugNoController" in dir(sys) and sys.debugNoController:
    from layer2.testbed.hostctl import SdnControllerClientL2Forward, SdnControllerClientCallback
else:
    from net.es.netshell.controller.client import SdnControllerClientL2Forward, SdnControllerClientCallback

from layer2.testbed.hostctl import connectgri,getdatapaths,setmeter,swconnect,connecthostbroadcast,deleteforward,connectentryfanout,connectexitfanout,setcallback,clearcallback

import threading

sites = {
    'wash' : {'name':"wash",'pop':'WASH','hosts':{'wash-tbn-1':{'interface':'eth11'}},'connected':{}},
    'amst' : {'name':"amst",'pop':'AMST','hosts':{'amst-tbn-1':{'interface':'eth17'}},'connected':{}},
    'cern' : {'name':"cern",'pop':'CERN','hosts':{'cern-272-tbn-1':{'interface':'eth14'}},'connected':{}},

    'aofa' : {'name':"aofa", 'pop':'AOFA','hosts':{'aofa-tbn-1':{'interface':'eth11'}}, 'connected':{}},
    'denv' : {'name':"denv", 'pop':'DENV','hosts':{'denv-tbn-1':{'interface':'eth11'}}, 'connected':{}},
    'star' : {'name':"star", 'pop':'STAR','hosts':{'star-tbn-4':{'interface':'eth17'}}, 'connected':{}}
}

def interconnect(site1,site2):
    """
    Given two sites, return a GRI to be used for VPN traffic between them.
    Assumes that the first applicable GRI is the one to be used.
    :param site1:
    :param site2:
    :return:
    """
    pop1 = site1['pop']
    pop2 = site2['pop']
    return interconnectpops(pop1,pop2)

def interconnectpops(pop1,pop2):
    """
    Given two POPs, return a GRI to be used to VPN traffic between them.
    Assumes that the first applicable GRI is the one to be used.
    :param pop1: Name of POP
    :param pop2: Name of POP
    :return:
    """
    (x,gri) = getcoregris(pop1.upper(),pop2.upper()).items()[0]
    return gri


if not 'VPNlock' in globals():
    VPNlock = threading.Lock()
    globals()['VPNlock'] = VPNlock

if not 'VPNMAT' in globals():
    VPNMAT = False
    globals()['VPNMAT'] = VPNMAT

def newVid():
    with globals()['VPNlock']:
        while True:
            v = random.randint(1,65535)
            if not v in globals()['vpnIndexById']:
                return v

class VpnCallback(SdnControllerClientCallback):
    def __init__(self, name):
        self.logger = logging.getLogger("VpnCallback")
        self.logger.setLevel(logging.INFO)
        self.logger.info("VpnCallback created")
        self.name = name
    def packetInCallback(self, dpid, inPort, payload):
        """
        Receive a PACKET_IN callback
        """
        # print "VpnCallback entry name", self.name, "dpid", dpid, "inPort", inPort, "payload", payload
        # Decode the callback.  First get the switch
        self.logger.info("PACKET_IN")
        switch = None
        hexdpid = binascii.hexlify(dpid)
        # topo global
        if not 'topo' in globals():
            self.logger.error("No topo object")
        for sw in topo.builder.switchIndex.values():
            if 'dpid' in sw.props.keys() and binascii.hexlify(sw.props['dpid']) == hexdpid:
                switch = sw
                break
        if switch == None:
            self.logger.error("Can't find switch " + str(dpid))
            return
        enosSwitch = switch.props['enosNode']

        # Now find the port
        if inPort not in switch.props['ports'].keys():
            self.logger.error("Can't find port " + inPort + " on switch " + switch.name)
            return
        port = switch.props['ports'][inPort]
        enosPort = port.props['enosPort']

        # Figure out how to print this
        print "VpnCallback decode switch", switch.name, "port", port.name
        self.logger.info("VpnCallback decode switch " + switch.name + " port " + port.name)
        return

# Start callback if we don't have one already
if not 'VPNcallback' in globals():
    VPNcallback = VpnCallback("MP-VPN Service")
    setcallback(VPNcallback)
    globals()['VPNcallback'] = VPNcallback
    print "VPNcallback set"

class VPNService(Resource):
    def __init__(self):
        Resource.__init__(self,"ServicePersistentState","net.es.netshell.api.Resource")
        self.container = Container.getContainer("MultiPointVPNService")
        if self.container == None:
            # First time the service is running initialize it.
            self.create()
            self.saveService()
        else:
            self.loadService()


    def create(self):
        # Creates the VPN service container
        Container.createContainer("MultiPointVPNService")
        self.container = Container.getContainer("MultiPointVPNService")
        self.vpns = []

    def saveService(self):
        cache = globals()['vpns']
        for vpn in cache:
            vpn.saveVPN()
            if not vpn.getResourceName() in self.vpns:
                self.vpns.append(vpn.getResourceName())
        self.properties['vpns'] = str(self.vpns)
        try:
            self.save(self.container)
        except:
            print "Failed to save VPN Service"

    def loadService(self):
        stored = self.container.loadResource(self.getResourceName())
        mapResource (obj=self,resource=stored)
        self.vpns = eval(self.properties['vpns'])
        cache = globals()['vpns']
        cacheIndex = globals()['vpnIndex']
        for name in self.vpns:
            if not name in cacheIndex:
                stored = self.loadVPN(name)
                vpn = VPN(stored.getResourceName())
                mapResource(obj=vpn,resource=stored)
                cache.append(vpn)
                cacheIndex[name] = vpn
                globals()['vpnIndexById'][vpn.vid] = vpn

    def saveVPN(self,vpn):
        if not vpn.name in self.vpns:
            self.vpns.append(vpn.name)
        if vpn.name == "ServicePersistentState":
            # a vpn cannot have the same name as the VPNService resource name.
            raise ValueError("VPN instances cannot this reserved name.")
        self.container.saveResource(vpn)

    def loadVPN(self,vpnName):
        return self.container.loadResource(vpnName)


class VPN(Resource):
    def __init__(self,name):
        Resource.__init__(self,name,"net.es.netshell.api.Resource")
        self.vid = newVid()
        self.name = name
        self.pops = {}              # pop name -> pop
        self.vpnsites = {}          # site name -> site
        self.popflows = {}          # pop name -> (FlowHandle)
        self.siteflows = {}         # site name -> (FlowHandle)
        self.hostflows = {}         # host name -> (FlowHandle)
        self.entryfanoutflows = {}  # host name -> FlowHandle
        self.exitfanoutflows = {}   # exit pop name -> (entry pop name, FlowHandle)
        self.priority = "low"
        self.meter = 3
        self.lock = threading.Lock()
        self.mat = MAT(self.vid)

    def saveVPN(self):
        self.properties['vid'] = self. vid
        self.properties['priority'] = self.priority
        self.properties['meter'] = self.meter
        self.properties['mat'] = str(self.mat.serialize())
        tmp = []
        for p in self.pops:
            tmp.append(p)
        self.properties['pops'] = str(tmp)
        self.properties['vpnsites'] = str(self.vpnsites)
        self.properties['entryfanoutflows'] = str(self.entryfanoutflows)
        self.properties['exitfanoutflows'] = str(self.exitfanoutflows)
        globals()['vpnService'].saveVPN(self)

    def loadVPN(self):
        stored = self.container.loadResource(self.getResourceName())
        mapFromJavaObject(pyobj=self,jobj=stored)

        topo = globals()['topo']
        self.name = self.getResourceName()
        self.vid = self.properties['vid']
        self.priority = self.properties['priority']
        self.meter = self.properties['meter']
        tmp = eval(self.properties['pops'])
        self.pops={}
        for p in tmp:
            self.pops[p] = topo.builder.popIndex[p]
        self.vpnsites = eval (self.properties['vpnsites'])
        self.exitfanoutflows = eval (self.properties['exitfanoutflows'])
        self.entryfanoutflows = eval (self.properties['entryfanoutflows'])
        self.mat = MAT.deserialize(self.properties['mat'])

    def getsite(self,host):
        for (s,site) in self.vpnsites.items():
            if host['name'] in site['hosts']:
                return site
        return None

    def addpop(self,pop):
        rc = True

        with self.lock:

            fhlist = [] # List of FlowHandles for this POP

            # We need to make sure that meter(s) are set correctly on the switches in the POP.
            # In particular we need to do this on Corsas before pushing flows to it that reference
            # any of the meters we use here.  This code is a bit of a hard-coded hack, but it'll
            # have to do until we can figure out what's the desired behavior.  Note that we can
            # set a meter multiple times.  It is however a requirement that the driver needs to
            # have a set a meter before a flow references it; in particular we cannot use an
            # external mechanism (e.g. CLI) to set the meter and then try to have the driver
            # push a flow that references it.
            sw = pop.props['hwSwitch']
            meter = self.meter
            rc = setmeter(sw, meter, 0, 0, 0, 0)
            # if not rc:

            # Iterate over the existing POPs to set up entries to handle broadcast traffic
            # between the POP being added and the existing POPs.  These all go in the
            # hardware switches.
            broadcastmac = "FF:FF:FF:FF:FF:FF"
            broadcastmac_mat = broadcastmac
            if VPNMAT:
                broadcastmac_mat = self.generateMAC(broadcast)
            for (remotepopname, remotepop) in self.pops.items():
                gri = interconnectpops(pop.name.upper(), remotepop.name.upper())
                fhs = swconnect(pop, remotepop, broadcastmac_mat, gri, self.meter)
                self.popflows[remotepop.name].extend(fhs)
                fhlist.extend(fhs)

            # This POP is now added.
            self.pops[pop.name] = pop
            self.popflows[pop.name] = fhlist

            # print "addpop ending with pop flow handles", self.popflows[pop.name]

        return rc
    def delpop(self,pop):
        # Ideally we would undo the meter setting that was done in addpop.  But at this point
        # we don't have a mechanism for handling the fact that a meter might be in use by
        # flows for multiple VPNs.  If we indiscriminantly delete a meter, we might blow away
        # flows in use by some other, unrelated VPNs.  This is solely an issue on the Corsas
        # at this point.
        if self.popflows(pop.name):
            self.deletefhs(self.popflows[pop.name])
            del self.popflows[pop.name]
        del self.pops[pop.name]
        return True
    def addsite(self,site):
        self.vpnsites[site['name']] = site
        self.siteflows[site['name']] = []
        return True
    def delsite(self,site):
        if self.siteflows(site['name']):
            self.deletefhs(self.siteflows[site['name']])
            del self.siteflows[site['name']]
        del self.vpnsites[site['name']]
        return True
    def generateMAC(self,host):
        interface = getdatapaths(host)[0]
        mac = interface['mac']
        # MAT.translate is idempotent: if a translated mac has already been allocated for a given mac, the
        # function will not generate a new mac but instead return the previously generated mac.
        newmac = self.mat.translate(mac)
        return str(newmac)
    def generateBroadcastMAC(self):
        return str(self.mat.translate("FF:FF:FF:FF:FF:FF"))
    def deletefhs(self, fhs):
        for f in fhs.items():
            if f.isValid():
                deleteforward(f)
                f.invalidate()

    def addhost(self,host,vlan):
        with self.lock:
            hostsite = self.getsite(host)
            hostsite['connected'][host['name']] = vlan
            host_mat = None
            broadcast_mat = "FF:FF:FF:FF:FF:FF"
            if VPNMAT:
                host_mat = self.generateMAC(host)
                broadcast_mat = self.generateBroadcastMAC()
            self.hostflows[host['name']] = []

            # Iterate over all sites that are "remote" to this host
            for (s,site) in self.vpnsites.items():
                if site['name'] == hostsite['name']:
                    # XXX Need to add forwarding entries to/from other hosts at the same site?
                    continue
                connected = site['connected']
                gri = interconnect(hostsite, site)
                # For each of those sites, iterate over the hosts at that site
                for (r,remotevlan) in connected.items():
                    remotehost = tbns[r]
                    remotehost_mat = None
                    if VPNMAT:
                        remotehost_mat =  self.generateMAC(remotehost)
                    fhlist = []

                    # Add flows coming from other site/host
                    fhs = connectgri(host=host,
                               host_rewritemac= host_mat,
                               hostvlan=vlan,
                               remotehost=remotehost,
                               remotehostvlan = remotevlan,
                               gri=gri,meter=self.meter)
                    if fhs != None:
                        fhlist.extend(fhs)
                    # Add flows going to other site/host
                    fhs = connectgri(host=remotehost,
                               host_rewritemac= remotehost_mat,
                               hostvlan=remotevlan,
                               remotehost=host,
                               remotehostvlan=vlan,
                               gri=gri,
                               meter=self.meter)
                    if fhs != None:
                        fhlist.extend(fhs)

                    self.hostflows[host['name']].extend(fhlist)
                    self.hostflows[remotehost['name']].extend(fhlist)

            # Add flows to get broadcast traffic between the host and the software switch.
            # Technically these flows are per-site not per-host,
            # but VLANs are currently (incorrectly?) assigned on the basis of a host.
            pop = self.pops[hostsite['pop'].lower()]
            connecthostbroadcast(localpop= pop,
                                 host= host,
                                 hostvlan= vlan,
                                 meter= self.meter,
                                 broadcast_rewritemac= broadcast_mat)

            # Create entry fanout flow on the software switch.  This flow fans out traffic
            # from the host/site to other hosts/sites on the same POP, as well as to all the
            # other POPs.
            # XXX need to re-run this part if we add another host/site to this POP or add
            # another POP
            forwards = []
            localpopname = hostsite['pop'].lower()
            localpop = self.pops[localpopname]

            # Locate all other hosts/sites on this POP
            for (otherhostname, otherhostvlan) in hostsite['connected'].items():
                if otherhostname != host['name']:
                    fwd = SdnControllerClientL2Forward()
                    fwd.outPort = "0" # to be filled in by connectentryfanout
                    fwd.vlan = otherhostvlan
                    fwd.dstMac = "FF:FF:FF:FF:FF:FF"
                    forwards.append(fwd)

            # Locate other POPs
            for (otherpopname, otherpop) in self.pops.items():
                if otherpopname != localpopname:
                    gri = interconnectpops(localpopname, otherpopname)
                    (corename, coredom, coreport, corevlan) = getgrinode(gri, localpop.props['coreRouter'].name)
                    fwd = SdnControllerClientL2Forward()
                    fwd.outPort = "0" # to be filled in by connectentryfanout
                    fwd.vlan = int(corevlan)
                    fwd.dstMac = broadcast_mat
                    forwards.append(fwd)

            # If we've already made an entry fanout flow for this host, then delete it.
            if host['name'] in self.entryfanoutflows:
                oldfh = self.entryfanoutflows[host['name']]
                if oldfh.isValid():
                    deleteforward(oldfh)
                    del self.entryfanoutflows[host['name']]
                    oldfh.invalidate()
            fh = connectentryfanout(localpop= pop,
                                    host= host,
                                    hostvlan= vlan,
                                    forwards= forwards,
                                    meter= self.meter,
                                    mac= broadcast_mat)
            if fh != None:
                self.entryfanoutflows[host['name']] = fh
                self.hostflows[host['name']].append(fh)

            # Create exit fanout flows on the software switch.  This flow fans out traffic
            # from other POPs, to hosts/sites on this POP.
            # XXX need to re-run this part if we add another host/site to this POP or
            # add another POP
            # XXX Note that for a given port, the exit fanout flows are all identical,
            # except that their match VLAN numbers are different, corresponding to the VLAN
            # of the core OSCARS circuits.  We might possibly be able to collapse these down
            # to a single flow rule if we don't try to match on the VLAN tag.  It's not clear
            # if we want to do this or not, there might be some security and/or reliability
            # implications to doing this change.
            forwards = []
            if localpopname in self.exitfanoutflows:
                exitfanoutflows = self.exitfanoutflows[localpopname]
            else:
                exitfanoutflows = {}
                self.exitfanoutflows[localpopname] = exitfanoutflows
            # Locate all hosts/sites on this POP.
            for (otherhostname, otherhostvlan) in hostsite['connected'].items():
                fwd = SdnControllerClientL2Forward()
                fwd.outPort = "0" # to be filled in by connectexitfanout
                fwd.vlan = int(otherhostvlan)
                fwd.dstMac = "FF:FF:FF:FF:FF:FF"
                forwards.append(fwd)

            # Iterate over source POPs
            for (srcpopname, srcpop) in self.pops.items():
                if srcpopname != localpopname:
                    # Get the VLAN coming from the core for this source POP
                    gri = interconnectpops(localpopname, srcpopname)
                    (corename, coredom, coreport, corevlan) = getgrinode(gri, localpop.props['coreRouter'].name)

                    # If we already made an exit fanout flow for this source POP, delete it
                    if srcpopname in exitfanoutflows:
                        oldfh = exitfanoutflows[srcpopname]
                        if oldfh.isValid():
                            deleteforward(oldfh)
                            del exitfanoutflows[srcpopname]
                            oldfh.invaldate()
                    fh = connectexitfanout(localpop= pop,
                                           corevlan= corevlan,
                                           forwards= forwards,
                                           meter= self.meter,
                                           mac= broadcast_mat)
                    if fh != None:
                        exitfanoutflows[srcpopname] = fh
                        self.popflows[srcpopname].append(fh)

        # print "addhost ending with host flow handles", self.hostflows[host['name']]

        return True

    def delhost(self,host):
        if self.hostflows(host['name']):
            self.deletefhs(self.hostflows(host['name']))
            del self.hostflows[host['name']]
        return True

    def setpriority(self,priority):
        """
        Set the priority for this VPN's flows.
        Can be either "high" or low, but in the current implementation this must be
        set before any POPs, sites, or hosts are added.
        """
        self.priority = priority
        if priority == 'high':
            self.meter = 5
        else:
            self.meter = 3

    def getpriority(self):
        return self.priority


def usage():
    print "usage:"
    print "vpn create <vpn name>"
    print "vpn delete <vpn name>"
    print "vpn kill <vpn name>"
    print "vpn load $conf"
    print "vpn <vpn name> execute"
    print "vpn <vpn name> save $conf"
    print "vpn <vpn name> getprio"
    print "vpn <vpn name> setprio"
    print "vpn <vpn name> addpop <pop name>"
    print "vpn <vpn name> delpop <pop name>"
    print "vpn <vpn name> addsite <site name>"
    print "vpn <vpn name> delsite <site name>"
    print "vpn <vpn name> addhost <host name> vlan <vlan>"
    print "vpn <vpn name> delhost <host name>"
    print "vpn <vpn name> tapsite <site name>"
    print "vpn <vpn name> untapsite <site name>"
    print "vpn <vpn name> taphost <host name>"
    print "vpn <vpn name> untaphost <host name>"
    print "vpn <vpn name> tapmac <MAC>"
    print "vpn <vpn name> untapmac <MAC>"
    print "vpn <vpn name> settimeout <secs>"
    print "vpn <vpn name> visualize $conf"
    print "vpn mat [<on|off>] Displays the MAC Address Translation feature, turn it on or off."
    print "Note: <vpn name> should not be any keyword such as create, delete, kill, or load"

def toint(s):
    try:
        return int(s)
    except:
        print "%s is an invalid integer" % s
        sys.exit(1)
def tobool(s):
    return s.lower() in ('yes', 'true', '1', 't')
def tofloat(s):
    try:
        return float(s)
    except:
        print "%s is an invalid value" % s
        sys.exit(1)
def tomac(s):
    try:
        mac = MACAddress(int(s))
    except:
        try:
            mac = MACAddress(s)
        except:
            print "%s is an invalid MAC address" % s
            sys.exit(1)
    return mac
def get(l, d, index):
    """
    :param l: a list of objects
    :param d: a dict of objects
    :param index: str; could be number or name
    """
    try:
        return l[int(index)]
    except:
        pass # not found
    try:
        return d[index]
    except:
        print "%s not found" % index
        sys.exit(1)
def tovpn(s):
    return get(vpns, vpnIndex, s)
def topop(s):
    return get(topo.builder.pops, topo.builder.popIndex, s)
def tosite(s):
        if s in sites:
            return sites[s]
        else:
            return None
def tohost(s):
    return tbns[s]


def addVpn(vpn):
    vpns.append(vpn)
    vpnIndex[vpn.name] = vpn
    globals()['vpnIndexById'][vpn.vid] = vpn



def create(vpnname):
    if vpnname in vpnIndex:
        print "vpn %r exists already" % vpnname
        return
    vpn = VPN(vpnname)
    addVpn(vpn)
    print "VPN %s is created successfully." % vpn.name

def delete(vpnname):
    if not vpnname in vpnIndex:
        print "vpn name %s not found" % vpnname
        return
    vpn = vpnIndex[vpnname]
    vpnIndex.pop(vpn.name)
    vpns.remove(vpn)
    globals()['vpnIndexById'].remove(vpn.vid)

def kill(vpnname):
    if not vpnname in vpnIndex:
        print "vpn name %s not found" % vpnname
        return
    vpn = vpnIndex[vpnname]
    for (site, hosts, siteVlan) in vpn.props['participantIndex'].values():
        for host in hosts:
            delhost(vpn, host)
        delsite(vpn, site)
    delete(vpnname)

def execute(vpn):
    return

def addpop(vpn, pop):
    if not vpn.addpop(pop):
        print "Error while adding pop."
        return
    print "Pop %s is added into VPN %s successfully." % (pop.name, vpn.name)

def delpop(vpn, pop):
    if not vpn.delpop(pop):
        print "Error while deleting pop."
        return
    print "Pop %s had been removed from VPN %s successfully." % (pop.name, vpn.name)

def addsite(vpn, site):
    if not vpn.addsite(site):
        print "something's wrong while adding the site."
        # possible issues: duplicated site
        return
    print "The site %s is added into VPN %s successfully" % (site['name'], vpn.name)

def delsite(vpn, site):
    if not vpn.checkSite(site):
        print "site not found in the vpn"
        return
    vpn.delsite(site)

def addhost(vpn, host,vlan):
    if not vpn.addhost(host,vlan):
        print "something wrong while adding the host; Please make sure that the site of the host joined the VPN."
        return

    print "The host %s is added into VPN %s successfully" % (host['name'], vpn.name)

def delhost(vpn, host):
    if not vpn.delHost(host):
        print "something wrong while deleting the host; Please make sure that the host joined the VPN."
        return

def tapsite(vpn, site):
    print "not implemented"

def untapsite(vpn, site):
    print "not implemented"

def taphost(vpn, host):
    print "not implemented"

def untaphost(vpn, host):
    print "not implemented"

def tapmac(vpn, mac):
    print "not implemented"

def untapmac(vpn, mac):
    print "not implemented"

def settimeout(vpn, timeout):
    if timeout < 0:
        print "invalid timeout"
        return
    print "not implemented"

def main():
    global VPNMAT
    try:
        command = sys.argv[1].lower()
        if command == 'create':
            vpnname = sys.argv[2]
            create(vpnname)
        elif command == 'delete':
            vpnname = sys.argv[2]
            delete(vpnname)
        elif command == 'kill':
            vpnname = sys.argv[2]
            kill(vpnname)
        elif command == 'load':
            globals()['vpnService'].loadService()
        elif command == "save":
            globals()['vpnService'].saveService()
        elif command == "mat":
            if 'on' in sys.argv:
                VPNMAT = True
            if 'off' in sys.argv:
                VPNMAT = False
            state = {True:'on',False:'off'}
            print "MAC Address Translation feature is",state[VPNMAT]
        else:
            vpn = get(vpns, vpnIndex, sys.argv[1])
            command = sys.argv[2].lower()
            if command == 'execute':
                execute(vpn)
            elif command == 'getprio':
                prio = vpn.getpriority()
                print prio
            elif command == 'setprio':
                vpn.setpriority(sys.argv[3])
            elif command == 'addpop':
                if not sys.argv[3] in topo.builder.popIndex:
                    print "unknown SDN POP"
                    return
                pop = topo.builder.popIndex[sys.argv[3]]
                addpop(vpn, pop)
            elif command == 'delpop':
                pop = topop(sys.argv[3])
                delpop(vpn, pop)
            elif command == 'addsite':
                site = tosite(sys.argv[3])
                if site == None:
                    print "unknown site"
                    return
                addsite(vpn, site)
            elif command == 'delsite':
                site = tosite(sys.argv[3])
                if site == None:
                    print "unknown site"
                    return
                delsite(vpn, site)
            elif command == 'addhost':
                host = tohost(sys.argv[3])
                vlan = sys.argv[5]
                addhost(vpn, host,vlan)
            elif command == 'delhost':
                host = tohost(sys.argv[3])
                if host == None:
                    return
                delhost(vpn, host)
            elif command == 'tapsite':
                site = tosite(sys.argv[3])
                if site == None:
                    print "unknown site"
                    return
                tapsite(vpn, site)
            elif command == 'untapsite':
                site = tosite(sys.argv[3])
                if site == None:
                    print "unknown site"
                    return
                untapsite(vpn, site)
            elif command == 'taphost':
                host = tohost(sys.argv[3])
                taphost(vpn, host)
            elif command == 'untaphost':
                host = tohost(sys.argv[3])
                untaphost(vpn, host)
            elif command == 'tapmac':
                mac = tomac(sys.argv[3])
                tapmac(vpn, mac)
            elif command == 'untapmac':
                mac = tomac(sys.argv[3])
                untapmac(vpn, mac)
            elif command == 'settimeout':
                timeout = tofloat(sys.argv[3])
                settimeout(vpn, timeout)
            else:
                print "unknown command"
                usage()
    except:
        #        print "Invalid arguments"
        #        usage()
        raise

# Retrieve topology
if not 'topo' in globals() or topo == None:
    topo = TestbedTopology()
    globals()['topo'] = topo
if 'vpnIndex' not in globals() or vpnIndex == None:
    vpnIndex = {}
    globals()['vpnIndex'] = vpnIndex
if 'vpnIndexById' not in globals() or vpnIndexById == None:
    vpnIndexById = {}
    globals()['vpnIndexById'] = vpnIndexById
if 'vpns' not in globals() or vpns == None:
    vpns = []
    globals()['vpns'] = vpns

if __name__ == '__main__':
    if not 'topo' in globals() or topo == None:
        topo = TestbedTopology()
        globals()['topo'] = topo
    if 'vpnIndex' not in globals() or vpnIndex == None:
        vpnIndex = {}
        globals()['vpnIndex'] = vpnIndex
    if 'vpns' not in globals() or vpns == None:
        vpns = []
        globals()['vpns'] = vpns

    if BootStrap.getBootStrap().getDataBase() != None:
        # NetShell is configured to use a database.
        vpnService = VPNService()
        globals()['vpnService'] = vpnService
    else:
        globals()['vpnService'] = None
    main()
