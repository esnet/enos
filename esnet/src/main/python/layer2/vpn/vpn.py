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
from layer2.common.mac import MACAddress
from layer2.testbed.hostctl import connectgri,getdatapaths,setmeter,swconnect
from layer2.testbed.oscars import getgri,getcoregris
from layer2.testbed.topology import TestbedTopology
from layer2.testbed.builder import tbns
from layer2.vpn.mat import MAT

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

if not 'VPNinstances' in globals() or VPNinstances == None:
    VPNinstances = {}
    globals()['VPNinstances'] = VPNinstances

if not 'VPNindex' in globals():
    VPNindex = 0
    globals()['VPNindex'] = VPNindex

if not 'VPNlock' in globals():
    VPNlock = threading.Lock()
    globals()['VPNlock'] = VPNlock

if not 'VPNMAT' in globals():
    VPNMAT = False
    globals()['VPNMAT'] = VPNMAT

class VPN():

    def __init__(self,name):
        global VPNinstances, VPNindex, VPNlock
        with VPNlock:
            VPNinstances['name'] = self
            self.vid = VPNindex
            VPNindex += 1
        self.name = name
        self.pops = {}
        self.vpnsites = {}
        self.priority = "low"
        self.meter = 3
        self.lock = threading.Lock()
        self.mat = MAT(self.vid)

    def getsite(self,host):
        for (s,site) in self.vpnsites.items():
            if host['name'] in site['hosts']:
                return site
        return None
    def addpop(self,pop):
        rc = True

        with self.lock:

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
                swconnect(pop, remotepop, broadcastmac_mat, gri, self.meter)

            # This POP is now added.
            self.pops[pop.name] = pop

        return rc
    def delpop(self,pop):
        # Ideally we would undo the meter setting that was done in addpop.  But at this point
        # we don't have a mechanism for handling the fact that a meter might be in use by
        # flows for multiple VPNs.  If we indiscriminantly delete a meter, we might blow away
        # flows in use by some other, unrelated VPNs.  This is solely an issue on the Corsas
        # at this point.
        del self.pops[pop.name]
        return True
    def addsite(self,site):
        self.vpnsites[site['name']] = site
        return True
    def delsite(self,site):
        del self.vpnsites[site['name']]
        return True
    def generateMAC(self,host):
        interface = getdatapaths(host)[0]
        mac = interface['mac']
        # MAT.translate is idempotent: if a translated mac has already been allocated for a given mac, the
        # function will not generate a new mac but instead return the previously generated mac.
        newmac = self.mat.translate(mac)
        return str(newmac)

    def addhost(self,host,vlan):
        with self.lock:
            hostsite = self.getsite(host)
            hostsite['connected'][host['name']] = vlan
            # Iterate over all sites that are "remote" to this host
            for (s,site) in self.vpnsites.items():
                if site['name'] == hostsite['name']:
                    # XXX Need to add forwarding entries to/from other hosts at the same site?
                    continue
                connected = site['connected']
                # For each of those sites, iterate over the hosts at that site
                for (r,remotevlan) in connected.items():
                    gri = interconnect(hostsite,site) # XXX can this be in the site loop?
                    remotehost = tbns[r]
                    host_mat = None
                    remotehost_mat = None
                    if VPNMAT:
                        host_mat = self.generateMAC(host)
                        remotehost_mat =  self.generateMAC(remotehost)
                    # Add flows coming from other site/host
                    connectgri(host=host,
                               host_rewritemac= host_mat,
                               hostvlan=vlan,
                               remotehost=remotehost,
                               remotehostvlan = remotevlan,
                               gri=gri,meter=self.meter)
                    # Add flows going to other site/host
                    connectgri(host=remotehost,
                               host_rewritemac= remotehost_mat,
                               hostvlan=remotevlan,
                               remotehost=host,
                               remotehostvlan=vlan,
                               gri=gri,
                               meter=self.meter)

        return True
    def delhost(self,host):
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
            confname = sys.argv[2]
            load(confname)
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
    main()
