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
import java.lang.Thread
from layer2.common.mac import MACAddress
from layer2.testbed.vc import getvcnode
from layer2.testbed.topology import TestbedTopology
from layer2.testbed.builder import tbns
from layer2.vpn.mat import MAT
from layer2.common.utils import mapResource
from net.es.netshell.api import Resource,Container,ResourceAnchor
from net.es.netshell.boot import BootStrap
from net.es.enos.mpvpn import MultiPointVPNService,MultiPointVPNServiceFactory

import sys
from threading import Thread
import time

try:
    from net.es.netshell.controller.intf import EthernetFrame
    from net.es.netshell.controller.client import SdnControllerClient, SdnControllerClientL2Forward, SdnControllerClientCallback
    sys.debugNoController = False
except:
    print "WARNING: controller is not loaded."
    sys.debugNoController = True
    from layer2.testbed.hostctl import SdnControllerClient, SdnControllerClientL2Forward, SdnControllerClientCallback

from layer2.testbed.hostctl import connectgrimac,getdatapaths,setmeter,swconnect,connecthostbroadcast,deleteforward,connectentryfanoutmac,connectexitfanout,setcallback,clearcallback

import threading

# Site descriptors, showing attachments to pops
sites = {
    'wash' : {'name':"wash",'pop':'wash','hwport':'1'},
    'amst' : {'name':"amst",'pop':'amst','hwport':'2'},
    'cern' : {'name':"cern",'pop':'cern','hwport':'5'},

    'aofa' : {'name':"aofa",'pop':'aofa','hwport':'2'},
    'atla' : {'name':"atla",'pop':'atla','hwport':'2'},
    'denv' : {'name':"denv",'pop':'denv','hwport':'2'},
    'star' : {'name':"star",'pop':'star','hwport':'2'}
}

class VpnCallback(SdnControllerClientCallback):
    def __init__(self, name, vs):
        self.logger = logging.getLogger("VpnCallback")
        self.logger.setLevel(logging.INFO)
        self.logger.info("VpnCallback created")
        self.name = name
        self.vpnService = vs
        self.switchIndex = {}
        self.indexSwitches()

    def indexSwitches(self):
        # Index all the switches by DPID so we can find them
        nodes = self.vpnService.topology.loadResources({"resourceType" : "Node"})
        for n in nodes:
            if 'DPID' in n.properties.keys():
                self.switchIndex[n.properties['DPID']] = n

    def packetInCallback(self, dpid, inPort, payload):
        """
        Receive a PACKET_IN callback
        """
        # Decode the callback.  First get the switch
        print "### PACKET IN ###"
        switch = None
        hexdpid = binascii.hexlify(dpid)
        if hexdpid in self.switchIndex.keys():
            switch = self.switchIndex[hexdpid]
        if switch == None:
            self.logger.error("Can't find switch " + str(dpid))
            return

        # Now find the port
        if inPort not in switch.properties['Ports'].keys():
            self.logger.error("Can't find port " + inPort + " on switch " + switch.resourceName)
            return
        port = Container.fromAnchor(switch.properties['Ports'][inPort])

        frame = EthernetFrame.packetToFrame(payload)
        if frame == None:
            self.logger.error("Cannot parse Ethernet frame")
            return

        switchpopname = switch.properties['Pop']

        # Log the packet we got
        self.logger.info("VpnCallback decode switch " + switch.resourceName +
                         " (" + switchpopname + ") " +
                         " port " + inPort + " vlan " + str(frame.getVid()) +
                         " src " + EthernetFrame.byteString(frame.getSrcMac()) +
                         " dst " + EthernetFrame.byteString(frame.getDstMac()) +
                         " etherType " + hex(frame.getEtherType()))

        # Ignore some packets
        if frame.getEtherType() == EthernetFrame.ETHERTYPE_LLDP:
            self.logger.debug("LLDP frame ignored")
            return

        # Figure out the slice/service ID.  This comes from the mapped destination address
        # (going to be a broadcast address).  If it doesn't match our slice ID then drop.
        # XXX need to check this, not clear if the MACAddress constructor will DTRT.
        mac = MACAddress(frame.getDstMac())
        if (mac.getSid() != self.vpnService.sid):
            self.logger.debug("Destination address doesn't match, ignored")
            return

        # Figure out which VPN (if any) this belongs to
        vpn = None
        vpnsite = None

        # Iterate over all VPNs then all site attachments.
        # If we can match the POP and VLAN, then we've got a match for the site attachments
        # XXX There is probably a more efficient way to do this.
        # XXX Note we can't do any port-based matching because all of the traffic from the
        # hardware switch to the software switch shows up on the same port on the software
        # switch, which is the one generating the PACKET_IN message.

        for (x,v) in MultiPointVPNServiceFactory.getVpnService().vpnIndex.items():
            for (sitename,site) in v.vpnsites.items():
                if site['pop'] == switchpopname and int(v.vpnsitevlans[sitename]) == frame.getVid():
                    vpn = v
                    vpnsite = site
        if vpn == None:
            self.logger.error("Unable to find VPN or site for inbound packet")
            return

        # MAC layer address.  For some reason we don't understand, this needs to be converted from
        # unicode (?!?) to ASCII before we can really use it despite the fact these are all ASCII
        # characters.
        mac = EthernetFrame.byteString(frame.getSrcMac()).encode('ascii', 'ignore')

        self.logger.info("  Source vpn " + vpn.name + " site " + vpnsite['name'] + " src " + mac)
        if vpn.addhostbymac(vpnsite, mac):
            self.logger.info("Added host successfully")
        else:
            self.logger.error("Adding host failed")
        return

class VPNService(Container,MultiPointVPNService):
    def __init__(self):
        Resource.__init__(self,"MultiPointVPNService")
        print "MultiPoint VPN Service is starting"
        self.vpnIndex = {}
        self.vpnIndexById = {}
        self.topology = None
        self.coretopology = None
        self.lock = threading.Lock()
        self.properties['mat'] = True # Default.
        self.loadService()
        self.saveThread = Thread(target=self.autosave)
        self.saveThread.start()
        if self.topology != None:
            self.setscc()

    def setscc(self):
        self.SCC = SdnControllerClient()
        self.sccThread = Thread(target=self.SCC)
        self.sccThread.start()
        self.VPNcallback = VpnCallback("MP-VPN Service", self)
        setcallback(self.VPNcallback)
        self.SCC.setCallback(self.VPNcallback)

    def settopos(self, popstoponame, coretoponame):
        self.properties['topology'] = popstoponame
        self.topology = Container.getContainer(self.properties['topology'])
        self.properties['coretopology'] = coretoponame
        self.coretopology = Container.getContainer(self.properties['coretopology'])
        # We can now set up the callback
        self.setscc()
        self.saveService()

    def shutdown(self):
        self.saveThread.stop()
        if self.sccThread != None:
            self.sccThread.stop()
            self.SCC.clearCallback()
        MultiPointVPNServiceFactory.delete()

    def autosave(self):
        while True:
            if not self.topology == None:
                self.saveService()
                for (x,vpn) in self.vpnIndex.items():
                    vpn.saveVPN()
            time.sleep(60)

    def saveService(self):
        self.properties['sid'] = self.sid
        try:
            self.properties['topology'] = self.topology.getResourceName()
            self.properties['coretopology'] = self.coretopology.getResourceName()
            self.save()
        except:
            print "Failed to save VPN Service\n", sys.exc_info()[0]

    def loadService(self):
        stored = Container.getContainer(self.getResourceName())
        mapResource (obj=self,resource=stored)
        if 'topology' in self.properties:
            self.topology = Container.getContainer(self.properties['topology'])
        if 'coretopology' in self.properties:
            self.coretopology = Container.getContainer(self.properties['coretopology'])
        vpns = self.loadResources({"resourceType":"VPN"})
        for v in vpns:
            vpn = VPN(v.getResourceName())
            vpn.loadVPN(self)
            self.vpnIndex[v.getResourceName()] = vpn
            self.vpnIndexById[vpn.vid] = vpn
        if not 'mat' in self.properties:
            self.properties['mat'] = True

    def newVid(self):
        with self.lock:
            while True:
                v = random.randint(1,65535)
                if not v in self.vpnIndexById:
                    return v

    def getSite(self,s):
        global sites
        if s in sites:
            return sites[s]
        else:
            return None

    def getHost(self,s):
        return tbns[s]

    def addVpn(self,vpn):
        self.vpnIndex[vpn.name] = vpn
        self.vpnIndexById[vpn.vid] = vpn
        self.saveResource(vpn)

    def createVPN(self,vpnname):
        if vpnname in self.vpnIndex:
            return None
        vpn = VPN(vpnname,vs=self)
        self.vid = self.newVid()
        self.addVpn(vpn)
        return vpn

    def deleteVPN(self,vpnname):
        if not vpnname in self.vpnIndex:
            print "vpn name %s not found" % vpnname
            return
        vpn = self.vpnIndex[vpnname]
        for h in vpn.hostsites.keys():
            self.delhostbymac(vpn, h)
        for s in vpn.vpnsites.values():
            self.delsite(vpn, s)
        for p in vpn.pops.values():
            self.delpop(vpn, p)
        self.vpnIndex.pop(vpn.name)
        self.vpnIndexById.pop(vpn.vid)
        self.deleteResource(vpn)
        print "VPN %s removed successfully." % (vpn.name)
        return True

    def getVPN(self,vpnname):
        if not vpnname in self.vpnIndex:
            return None
        return self.vpnIndex[vpnname]

    def addPOP(self,vpn, pop):
        if not vpn.addpop(pop):
            return False
        return True

    def deletePOP(self,vpn, pop):
        if not vpn.delpop(pop):
            return False
        return True

    def addSite(self, vpn, site, vlan):
        if not vpn.addsite(site, vlan):
            # possible issues: duplicated site
            return False
        return True

    def deleteSite(self, vpn, site):
        if not vpn.delsite(site):
            return False
        return True

    def addhostbymac(self, vpn, site, mac):
        if not vpn.addhostbymac(site, mac):
            print "Error while adding host."
            return
        print "Host %s has been added into VPN %s successfully at site %s" % (mac, vpn.name, site['name'])

    def delhostbymac(self,vpn, mac):
        if not vpn.delhostbymac(mac):
            print "Error while deleting host."
            return

class VPN(Resource):
    def __init__(self,name,vs):
        Resource.__init__(self,name,"net.es.netshell.api.Resource")
        self.vs = vs
        self.vid = 0
        self.name = name
        self.pops = {}              # pop name -> pop
        self.vpnsites = {}          # site name -> site
        self.vpnsitevlans = {}      # site name -> vlan tag for attachment
        self.popflows = {}          # pop name -> (FlowHandle)
        self.siteflows = {}         # site name -> (FlowHandle)
        self.hostflows = {}         # host name -> (FlowHandle)
        self.entryfanoutflows = {}  # host name -> FlowHandle
        self.exitfanoutflows = {}   # exit pop name -> (entry pop name, FlowHandle)
        self.hostsites = {}         # MAC address / host -> site name
        self.priority = "low"
        self.meter = 3
        self.lock = threading.Lock()
        self.mat = MAT(sid=self.vpnService.sid, vid=self.vid)

        self.logger = logging.getLogger("VPN")
        self.logger.setLevel(logging.INFO)
        self.setResourceType("VPN")

    def saveVPN(self):
        self.properties['vid'] = self. vid
        self.properties['priority'] = self.priority
        self.properties['meter'] = self.meter
        self.properties['mat'] = str(self.mat.serialize())
        if not 'pops' in self.properties:
            self.properties['pops'] = {}
        for p in self.pops:
            self.properties['pops'][p] = p
        #self.properties['pops'] = tmp
        self.properties['vpnsites'] = str(self.vpnsites)
        self.properties['vpnsitevlans'] = str(self.vpnsitevlans)
        self.properties['entryfanoutflows'] = str(self.entryfanoutflows)
        self.properties['exitfanoutflows'] = str(self.exitfanoutflows)
        self.properties['hostsites'] = str(self.hostsites)
        MultiPointVPNServiceFactory.getVpnService().saveResource(self)

    def loadVPN(self,mpvpn):
        stored = mpvpn.loadResource(self.getResourceName())
        mapResource(obj=self,resource=stored)

        self.name = self.getResourceName()
        self.vid = self.properties['vid']
        self.priority = self.properties['priority']
        self.meter = self.properties['meter']
        self.pops={}
        for (n,p) in self.properties['pops'].items():
            self.pops[n] = mpvpn.topology.loadResource(n)
        self.vpnsites = eval (self.properties['vpnsites'])
        self.vpnsitevlans = eval (self.properties['vpnsitevlans'])
        self.exitfanoutflows = eval (self.properties['exitfanoutflows'])
        self.entryfanoutflows = eval (self.properties['entryfanoutflows'])
        self.hostsites = eval (self.properties['hostsites'])
        self.mat = MAT.deserialize(self.properties['mat'])

        self.vpnService = vpnService # global

    def interconnect(self, site1,site2): # XXX core topo!
        """
        Given two sites, return a GRI to be used for VPN traffic between them.
        Assumes that the first applicable GRI is the one to be used.
        :param site1:
        :param site2:
        :return: Link (Resource)
        """
        pop1 = site1['pop']
        pop2 = site2['pop']
        return self.interconnectpops(pop1,pop2)

    def interconnectpops(self, pop1,pop2): # XXX core topo!
        """
        Given two POPs, return a GRI to be used to VPN traffic between them.
        Assumes that the first applicable GRI is the one to be used.
        :param pop1: Name of POP
        :param pop2: Name of POP
        :return: Link (Resource)
        """
        vc = MultiPointVPNServiceFactory.getVpnService().coretopology.loadResource(pop1 + "--" + pop2)
        return vc

    def makeentryfanoutflows(self, localpop, hostmac, hostvlan, hostsite):
        # Create entry fanout flow on the software switch.  This flow fans out traffic
        # from the host/site to other hosts/sites on the same POP, as well as to all the
        # other POPs.
        # XXX need to re-run this part if we add another host/site to this POP or add
        # another POP
        forwards = []

        broadcast_mat = "FF:FF:FF:FF:FF:FF"
        if MultiPointVPNServiceFactory.getVpnService().properties['mat']:
            broadcast_mat = self.generateBroadcastMAC()

        # Locate all other sites on this POP.  For each of these, make a forwarding entry to it.
        for (othersitename, othersite) in self.vpnsites.items():
            if othersite['pop'] == localpop.resourceName and othersitename != hostsite['name']:
                fwd = SdnControllerClientL2Forward()
                fwd.outPort = "0" # to be filled in by connectentryfanout
                fwd.vlan = int(self.vpnsitevlans[othersitename])
                fwd.dstMac =  broadcast_mat
                forwards.append(fwd)

        # Locate other POPs
        for (otherpopname, otherpop) in self.pops.items():
            if otherpopname != localpop.resourceName:
                vc = self.interconnectpops(localpop.resourceName, otherpopname)
                core = Container.fromAnchor(localpop.properties['CoreRouter'])
                coreresname = core.resourceName
                (corename, coredom, coreport, corevlan) = getvcnode(vc, coreresname)
                fwd = SdnControllerClientL2Forward()
                fwd.outPort = "0" # to be filled in by connectentryfanout
                fwd.vlan = int(corevlan)
                fwd.dstMac = broadcast_mat
                forwards.append(fwd)

        # If we've already made an entry fanout flow for this host, then delete it.
        if hostmac in self.entryfanoutflows:
            oldfh = self.entryfanoutflows[hostmac]
            if oldfh.isValid():
                deleteforward(oldfh)
                del self.entryfanoutflows[hostmac]
                oldfh.invalidate()
        fh = connectentryfanoutmac(localpop= localpop,
                                   hostmac= hostmac,
                                   hostvlan= hostvlan,
                                   forwards= forwards,
                                   meter= self.meter,
                                   mac= broadcast_mat)
        if fh != None:
            self.entryfanoutflows[hostmac] = fh
        return fh

    def addpop(self,pop):
        rc = True
        # See if we've already added the POP
        if pop.resourceName in self.pops:
            return False

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
            sw = Container.fromAnchor(pop.properties['HwSwitch'])
            meter = self.meter
            rc = setmeter(sw, meter, 0, 0, 0, 0)
            # if not rc:

            # Iterate over the existing POPs to set up entries to handle broadcast traffic
            # between the POP being added and the existing POPs.  These all go in the
            # hardware switches.
            broadcastmac = "FF:FF:FF:FF:FF:FF"
            broadcastmac_mat = broadcastmac
            if MultiPointVPNServiceFactory.getVpnService().properties['mat']:
                broadcastmac_mat = self.generateBroadcastMAC()
            for (remotepopname, remotepop) in self.pops.items():
                vc = self.interconnectpops(pop.getResourceName(), remotepop.getResourceName())
                fhs = swconnect(pop, remotepop, broadcastmac_mat, vc, self.meter)
                self.popflows[remotepop.getResourceName()].extend(fhs)
                fhlist.extend(fhs)

            # This POP is now added.
            self.pops[pop.resourceName] = pop
            self.popflows[pop.resourceName] = fhlist

            # Regenerate entry fanout flows for various hosts because they need to learn
            # about a new POP
            for (hostmac, hostsitename) in self.hostsites.items():
                hostsite = self.vpnsites[hostsitename]
                hostvlan = self.vpnsitevlans[hostsitename]
                localpop = self.pops[hostsite['pop']]
                fh = self.makeentryfanoutflows(localpop= localpop, hostmac= hostmac, hostvlan= hostvlan, hostsite= hostsite)
                if fh != None:
                    self.hostflows[hostmac].append(fh)

            # print "addpop ending with pop flow handles", self.popflows[pop.name]

        return rc

    def delpop(self,pop):
        # Ideally we would undo the meter setting that was done in addpop.  But at this point
        # we don't have a mechanism for handling the fact that a meter might be in use by
        # flows for multiple VPNs.  If we indiscriminantly delete a meter, we might blow away
        # flows in use by some other, unrelated VPNs.  This is solely an issue on the Corsas
        # at this point.
        if pop.resourceName in self.popflows.keys():
            self.deletefhs(self.popflows[pop.resourceName])
            del self.popflows[pop.resourceName]
        del self.pops[pop.resourceName]

        # Regenerate entry fanout flows for various hosts because they don't need to fanout
        # to this POP anymore
        for (hostmac, hostsitename) in self.hostsites.items():
            hostsite = self.vpnsites[hostsitename]
            hostvlan = self.vpnsitevlans[hostsitename]
            localpop = self.pops[hostsite['pop']]
            fh = self.makeentryfanoutflows(localpop= localpop, hostmac= hostmac, hostvlan= hostvlan, hostsite= hostsite)
            if fh != None:
                self.hostflows[hostmac].append(fh)

        return True

    def addsite(self,site,vlan):

        # If we've already added this site, don't do it again.
        # Note this is actually not a real requirement.  In theory it should be possible
        # to put multiple attachments to a single site, on different VLANs.  However
        # our implementation doesn't support that at this point, primarily because
        # we have some assumptions that each site only attaches once to a VPN.  This check
        # here is mostly to avoid violating these assumptions and getting us in trouble.
        if site['name'] in self.vpnsites:
            return False

        # Make sure the pop to which the site is attached is already a part of the VPN.
        # In theory we could implicitly add a POP whenever we add a site that needs it.
        if site['pop'].lower() not in self.pops:
            return False

        self.vpnsites[site['name']] = site
        self.vpnsitevlans[site['name']] = vlan
        self.siteflows[site['name']] = []

        broadcast_mat = "FF:FF:FF:FF:FF:FF"
        if MultiPointVPNServiceFactory.getVpnService().properties['mat']:
            broadcast_mat = self.generateBroadcastMAC()

        # Add flows to get broadcast traffic between the site and the software switch.
        pop = self.pops[site['pop']]
        fhs = connecthostbroadcast(localpop= pop,
                                   hwport_tosite= site['hwport'],
                                   sitevlan= vlan,
                                   meter= self.meter,
                                   broadcast_rewritemac= broadcast_mat)
        if fhs == None:
            return False
        self.siteflows[site['name']].extend(fhs)

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
        localpop = pop
        localpopname = localpop.resourceName

        forwards = []
        if localpopname in self.exitfanoutflows:
            exitfanoutflows = self.exitfanoutflows[localpopname]
        else:
            exitfanoutflows = {}
            self.exitfanoutflows[localpopname] = exitfanoutflows
        # Locate all sites on this POP, including the one we're adding now.
        # Be ready to forward to their
        for (site2name, site2) in self.vpnsites.items():
            if (site2['pop'] == site['pop']):
                fwd = SdnControllerClientL2Forward()
                fwd.outPort = "0" # to be filled in by connectexitfanout
                fwd.vlan = int(self.vpnsitevlans[site2name])
                fwd.dstMac = broadcast_mat
                forwards.append(fwd)

        # Iterate over source POPs
        for (srcpopname, srcpop) in self.pops.items():
            if srcpopname != localpopname:
                # Get the VLAN coming from the core for this source POP
                vc = self.interconnectpops(localpopname, srcpopname)
                core = Container.fromAnchor(localpop.properties['CoreRouter'])
                coreresname = core.resourceName
                (corename, coredom, coreport, corevlan) = getvcnode(vc, coreresname)

                # If we already made an exit fanout flow for this source POP, delete it
                if srcpopname in exitfanoutflows:
                    oldfh = exitfanoutflows[srcpopname]
                    if oldfh.isValid():
                        deleteforward(oldfh)
                        del exitfanoutflows[srcpopname]
                        oldfh.invalidate()
                fh = connectexitfanout(localpop= pop,
                                       corevlan= corevlan,
                                       forwards= forwards,
                                       meter= self.meter,
                                       mac= broadcast_mat)
                if fh != None:
                    exitfanoutflows[srcpopname] = fh
                    self.popflows[srcpopname].append(fh)

        # Regenerate entry fanout flows for various hosts on this POP because they just
        # learned a new site.
        for (hostmac, hostsitename) in self.hostsites.items():
            hostsite = self.vpnsites[hostsitename]
            if hostsite['pop'] == localpopname:
                hostvlan = self.vpnsitevlans[hostsitename]
                localpop = self.pops[hostsite['pop']]
                fh = self.makeentryfanoutflows(localpop= localpop, hostmac= hostmac, hostvlan= hostvlan, hostsite= hostsite)
                if fh != None:
                    self.hostflows[hostmac].append(fh)

        return True
    def delsite(self,site):
        localpop = self.pops[site['pop']]
        localpopname = localpop.resourceName

        if site['name'] in self.siteflows.keys():
            self.deletefhs(self.siteflows[site['name']])
            del self.siteflows[site['name']]
        del self.vpnsites[site['name']]
        del self.vpnsitevlans[site['name']]

        # Regenerate entry fanout flows for various hosts on this POP because they need
        # to forget this site
        for (hostmac, hostsitename) in self.hostsites.items():
            hostsite = self.vpnsites[hostsitename]
            if hostsite['pop'] == localpopname:
                hostvlan = self.vpnsitevlans[hostsitename]
                localpop = self.pops[hostsite['pop']]
                fh = self.makeentryfanoutflows(localpop= localpop, hostmac= hostmac, hostvlan= hostvlan, hostsite= hostsite)
                if fh != None:
                    self.hostflows[hostmac].append(fh)


        return True
    def generateMAC2(self,mac):
        """
        Translate a MAC address.
        :param mac: MAC address to translate (intended to be a string but can be any valid type to MACaddress constructor
        :return: String
        """
        return str(self.mat.translate(mac))
    def generateBroadcastMAC(self):
        return str(self.mat.translate("FF:FF:FF:FF:FF:FF"))

    def deletefhs(self, fhs):
        for f in fhs:
            if f.isValid():
                deleteforward(f)
                f.invalidate()

    def addhostbymac(self,hostsite,hostmac):
        """
        Add a host by its MAC address
        :param hostsite: site descriptor structure (see global sites)
        :param hostmac: MAC address (string)
        :return: boolean True if successful
        """

        # Normalize MAC address to lower-case
        hostmac = hostmac.lower()

        with self.lock:

            # See if the host already exists
            if hostmac in self.hostsites.keys():
                # See if we're trying to add to the same site.  If so that might indicate a problem
                # with flows, since we shouldn't be getting PACKET_IN events for a host after it's
                # been added.
                #
                # If the host shows up at a different site, maybe it moved?  Not sure how to handle this
                # but for now take this as a failure.  We could try to delete the host from the old site
                # and add it at the new site.
                #
                # XXX This condition might change after we add NFV support
                if hostsite['name'] == self.hostsites[hostmac]:
                    self.logger.info("Host " + hostmac + " already exists at site " + hostsite['name'])
                    return True
                else:
                    self.logger.info("Host " + hostmac + " moved from site " + self.hostsites[hostmac] + " to site " + hostsite['name'])
                    return False

            vlan = self.vpnsitevlans[hostsite['name']] # get VLAN from the site attachment
            localpopname = hostsite['pop']
            localpop = self.pops[localpopname]
            host_mat = None
            broadcast_mat = "FF:FF:FF:FF:FF:FF"
            vpnService = MultiPointVPNServiceFactory.getVpnService();
            if vpnService.properties['mat']:
                host_mat = self.generateMAC2(hostmac)
            self.hostflows[hostmac] = []

            # Install flows for unicast traffic
            # Iterate over all other hosts in the VPN, set up pairwise flows to new host
            for (remotehostmac, remotesitename) in self.hostsites.items():

                # If the host is at this site, don't need to do anything
                if remotesitename == hostsite['name']:
                    continue

                remotesite = sites[remotesitename]

                vc = self.interconnect(hostsite, remotesite)
                remotevlan = self.vpnsitevlans[remotesite['name']]
                remotepop = self.pops[remotesite['pop']]

                remotehost_mat = None
                if vpnService.properties['mat']:
                    remotehost_mat =  self.generateMAC2(remotehostmac)
                fhlist = []

                # Add flows coming from other site/host
                fhs = connectgrimac(topology= vpnService.topology,
                                    hostmac= hostmac,
                                    siteport= hostsite['hwport'],
                                    sitevlan= vlan,
                                    sitepop= localpop,
                                    remotesiteport= remotesite['hwport'],
                                    remotesitevlan= remotevlan,
                                    vc= vc,
                                    meter= self.meter,
                                    host_rewritemac= host_mat)
                if fhs != None:
                    fhlist.extend(fhs)
                # Add flows going to other site/host
                fhs = connectgrimac(topology= vpnService.topology,
                                    hostmac= remotehostmac,
                                    siteport= remotesite['hwport'],
                                    sitevlan= remotevlan,
                                    sitepop= remotepop,
                                    remotesiteport= hostsite['hwport'],
                                    remotesitevlan= vlan,
                                    vc= vc,
                                    meter= self.meter,
                                    host_rewritemac= remotehost_mat)
                if fhs != None:
                    fhlist.extend(fhs)

                self.hostflows[hostmac].extend(fhlist)
                self.hostflows[remotehostmac].extend(fhlist)

            fh = self.makeentryfanoutflows(localpop, hostmac, vlan, hostsite)

            if fh != None:
                self.hostsites[hostmac] = hostsite['name']
                self.hostflows[hostmac].append(fh)

        # print "addhost ending with host flow handles", self.hostflows[host['name']]

        return True

    def delhostbymac(self,hostmac):

        # Normalize MAC address to lower-case
        hostmac = hostmac.lower()

        if hostmac in self.hostsites.keys():
            del self.hostsites[hostmac]
        else:
            return False

        if hostmac in self.hostflows.keys():
            self.deletefhs(self.hostflows[hostmac])
            del self.hostflows[hostmac]
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

def startup():
    MultiPointVPNServiceFactory.create(None)
    vpnService = MultiPointVPNServiceFactory.getVpnService()

    sid = int(sys.argv[2]) # service ID
    vpnService.sid = sid
    vpnService.saveService()

def usage():
    print "usage:"

    print "\tvpn startup"
    print "\t\tStarts the service."
    print "\tvpn shutdown"
    print "\tvpn settopos <popstopo> <coretopo>"
    print "\tvpn logging <file>"
    print "\tvpn create <vpn name>"
    print "\tvpn delete <vpn name>"
    print "\tvpn mat [<on|off>] Displays the MAC Address Translation feature, turn it on or off."
    print
    print "\tvpn <vpn name> getprio"
    print "\tvpn <vpn name> setprio"
    print "\tvpn <vpn name> addpop <pop name>"
    print "\tvpn <vpn name> delpop <pop name>"
    print "\tvpn <vpn name> addsite <site name> vlan <vlan>"
    print "\tvpn <vpn name> delsite <site name>"
    print "\tvpn <vpn name> addhostbymac <site name> mac <MAC>"
    print "\tvpn <vpn name> delhostbymac <MAC>"
    print "\tvpn <vpn name> visualize $conf"
    print "\tvpn <vpn name> listpops"
    print "\tvpn <vpn name> listsites"
    print "\tvpn <vpn name> listhosts"
    print "\tNote: <vpn name> should not be any keyword such as create, delete, or load"


def main():
    vpnService = MultiPointVPNServiceFactory.getVpnService()

    try:
        command = sys.argv[1].lower()
        if command == 'help':
            usage()
        elif vpnService == None and command != "startup" and command != "settopos":
            print "failed: VPNSerice is not running."
            return

        elif command == 'create':
            vpnname = sys.argv[2]
            vpn = vpnService.createVPN(vpnname)
            if vpn == None:
                print "vpn %r exists already" % vpnname
            else:
                print "VPN %s is created successfully." % vpn.name
        elif command == 'delete':
            vpnname = sys.argv[2]
            res = vpnService.deleteVPN(vpnname)
            if res:
                print "VPN %s removed successfully." % (vpnname)
            else:
                print "vpn name %s not found" % vpnname
        elif command == 'load':
            vpnService.loadService()
        elif command == "save":
            vpnService.saveService()
        elif command == "mat":
            if 'on' in sys.argv:
                vpnService.properties['mat'] = True
            if 'off' in sys.argv:
                vpnService.properties['mat'] = False
            state = {True:'on',False:'off'}
            print "MAC Address Translation feature is",state[vpnService.properties['mat']]
        elif command == "shutdown":
            vpnService.shutdown()
        elif command == "shutdown":
            if 't' in globals():
                globals()['t'].stop()
                del globals()['t']
            if 'VPNcallback' in globals():
                if 'SCC' in globals():
                    globals()['SCC'].clearCallback()
                del globals()['VPNcallback']
            if 'SCC' in globals():
                del globals()['SCC']
        elif command == "logging":
            logname = sys.argv[2]
            logging.basicConfig(format='%(asctime)s %(levelname)8s %(message)s', filename=logname, filemode='a', level=logging.INFO)
            logging.info("test")
        elif command == 'settopos':
            popstoponame = sys.argv[2]
            coretoponame = sys.argv[3]
            vpnService.settopos(popstoponame, coretoponame)
        elif command == 'listvpns':
            print "%20s" % ("VPN")
            for name in vpnService.vpnIndex:
                print "%20s" % name
        else:
            vpn = vpnService.getVPN(sys.argv[1])
            command = sys.argv[2].lower()
            if command == 'getprio':
                prio = vpn.getpriority()
                print prio
            elif command == 'setprio':
                vpn.setpriority(sys.argv[3])
            elif command == 'addpop':
                pop = vpnService.topology.loadResource(sys.argv[3])
                if pop == None:
                    print "unknown SDN POP"
                    return
                res = vpnService.addPOP(vpn, pop)
                if res:
                    print "POP %s has been added into VPN %s successfully." % (pop.resourceName, vpn.name)
                else:
                    print "Error while adding pop."

            elif command == 'delpop':
                pop = vpnService.topology.loadResource(sys.argv[3])
                if pop == None:
                    print "unknown SDN POP"
                    return
                res = vpnService.deletePOP(vpn, pop)
                if res:
                    print "POP %s has been removed from VPN %s successfully." % (pop.resourceName, vpn.name)
                else:
                     print "Error while deleting pop."
            elif command == 'addsite':
                site = vpnService.getSite(sys.argv[3])
                if site == None:
                    print "unknown site"
                    return
                vlan = sys.argv[5]
                res = vpnService.addSite(vpn, site, vlan)
                if res:
                    print "Site %s has been added into VPN %s successfully." % (site['name'], vpn.name)
                else:
                    print "Error while adding site %s to VPN %s ." % (site['name'], vpn.name)
            elif command == 'delsite':
                site = vpnService.getSite(sys.argv[3])
                if site == None:
                    print "unknown site"
                    return
                res = vpnService.deleteSite(vpn, site)
                if res:
                    print "Site %s has been removed from VPN %s successfully." % (site['name'], vpn.name)
                else:
                    print "could not delete site"

            elif command == 'addhostbymac':
                sitename = sys.argv[3]
                if sitename not in vpn.vpnsites:
                    print "unknown site"
                    return
                site = vpn.vpnsites[sitename]
                mac = sys.argv[5]
                vpnService.addhostbymac(vpn, site, mac)
            elif command == 'delhostbymac':
                mac = sys.argv[3]
                vpnService.delhostbymac(vpn, mac)
            elif command == 'listhosts':
                print "%17s  %17s  %s" % ("MAC", "Translated MAC", "Site")
                for (hostmac, hostsite) in vpn.hostsites.items():
                    hostmacmat = hostmac
                    if vpnService.properties['mat']:
                        hostmacmat = vpn.generateMAC2(hostmac)
                    print "%17s  %17s  %s" % (hostmac, hostmacmat, hostsite)
            elif command == 'listsites':
                print "%6s  %6s  %20s  %8s  %4s" % ("Site", "POP", "Switch", "Port", "VLAN")
                for (sitename, site) in vpn.vpnsites.items():
                    popname = site['pop'] # string
                    pop = Container.fromAnchor(vpnService.topology.properties['Pops'][popname])
                    hwswitch = Container.fromAnchor(pop.properties['HwSwitch'])
                    hwswitchname = hwswitch.resourceName

                    hwport = site['hwport']
                    vlan = vpn.vpnsitevlans[sitename]
                    print "%6s  %6s  %20s  %8s  %4s" % (sitename, site['pop'], hwswitchname, hwport, vlan)
            elif command == 'listpops':
                print "%6s  %20s  %20s  %20s" % ("POP", "Core Router", "Hardware Switch", "Software Switch")
                for (popname, pop) in vpn.pops.items():
                    if BootStrap.getBootStrap().getDataBase() != None:
                        coreRouterName = pop.properties['CoreRouter']['resourceName']
                        hwSwitchName = pop.properties['HwSwitch']['resourceName']
                        swSwitchName = pop.properties['SwSwitch']['resourceName']
                    else:
                        coreRouterName = pop.props['coreRouter']
                        hwSwitchName = pop.props['hwSwitch']
                        swSwitchName = pop.props['swSwitch']
                    print "%6s  %20s  %20s  %20s" % (popname, coreRouterName, hwSwitchName, swSwitchName)
            else:
                print "unknown command"
                usage()
    except:
        #        print "Invalid arguments"
        #        usage()
        raise

if __name__ == '__main__':
    main()
