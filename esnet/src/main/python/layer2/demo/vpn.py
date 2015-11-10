#
# ENOS, Copyright (c) 2015, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov.
#
# NOTICE.  This software is owned by the U.S. Department of Energy.  As such,
# the U.S. Government has been granted for itself and others acting on its
# behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software
# to reproduce, prepare derivative works, and perform publicly and display
# publicly.  Beginning five (5) years after the date permission to assert
# copyright is obtained from the U.S. Department of Energy, and subject to
# any subsequent five (5) year renewals, the U.S. Government is granted for
# itself and others acting on its behalf a paid-up, nonexclusive, irrevocable,
# worldwide license in the Software to reproduce, prepare derivative works,
# distribute copies to the public, perform publicly and display publicly, and
# to permit others to do so.
#
from layer2.common.api import VPN

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
    print "vpn <vpn name> addhost <host name>"
    print "vpn <vpn name> delhost <host name>"
    print "vpn <vpn name> tapsite <site name>"
    print "vpn <vpn name> untapsite <site name>"
    print "vpn <vpn name> taphost <host name>"
    print "vpn <vpn name> untaphost <host name>"
    print "vpn <vpn name> tapmac <MAC>"
    print "vpn <vpn name> untapmac <MAC>"
    print "vpn <vpn name> settimeout <secs>"
    print "vpn <vpn name> visualize $conf"
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
    return get(topo.builder.siteIndex.values(), topo.builder.siteIndex, s)
def tohost(s):
    return get(topo.builder.hostIndex.values(), topo.builder.hostIndex, s)


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
    renderer = vpn.props['renderer']
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
    renderer = vpn.props['renderer']
    for pop in renderer.props['popIndex'].values():
        delpop(vpn, pop)
    delete(vpnname)

def execute(vpn):
    vpn.props['renderer'].execute()

def addpop(vpn, pop):
    print "Pop %s is added into VPN %s successfully." % (pop.name, vpn.name)

def delpop(vpn, pop):
    print "Pop %s had been removed from VPN %s successfully." % (pop.name, vpn.name)

def addsite(vpn, site):

    if not vpn.addSite(site):
        print "something's wrong while adding the site."
        # possible issues: duplicated site
        return
    print "The site %s is added into VPN %s successfully" % (site.name, vpn.name)

def delsite(vpn, site):
    siteVlan = vpn.props['participantIndex'][site.name][2]
    if not vpn.checkSite(site):
        print "site not found in the vpn"
        return
    vpn.delSite(site)

def addhost(vpn, host):
    print "vpn addhost",host
    if not vpn.addHost(host):
        print "something wrong while adding the host; Please make sure that the site of the host joined the VPN."
        return

    print "The host %s is added into VPN %s successfully" % (host.name, vpn.name)

def delhost(vpn, host):
    if not vpn.delHost(host):
        print "something wrong while deleting the host; Please make sure that the host joined the VPN."
        return
#    sitename = host.props['site'].name
#    siteRenderer = rendererIndex[sitename]
#    siteRenderer.delHost(host, vpn.props['participantIndex'][sitename][2])

def tapsite(vpn, site):
    vpn.props['renderer'].tapSiteCLI(site)

def untapsite(vpn, site):
    vpn.props['renderer'].untapSiteCLI(site)

def taphost(vpn, host):
    vpn.props['renderer'].tapHostCLI(host)

def untaphost(vpn, host):
    vpn.props['renderer'].untapHostCLI(host)

def tapmac(vpn, mac):
    vpn.props['renderer'].tapMacCLI(mac)

def untapmac(vpn, mac):
    vpn.props['renderer'].untapMacCLI(mac)

def settimeout(vpn, timeout):
    if timeout < 0:
        print "invalid timeout"
        return
    vpn.props['renderer'].setTimeout(timeout)

def main():
    if not 'topo' in globals():
        print 'Please run demo first'
        return
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
        else:
            vpn = get(vpns, vpnIndex, sys.argv[1])
            command = sys.argv[2].lower()
            if command == 'execute':
                execute(vpn)
            elif command == 'getprio':
                prio = vpn.getPriority()
                print prio
            elif command == 'setprio':
                vpn.setPriority(sys.argv[3])
            elif command == 'addpop':
                pop = topo.builder.popIndex[sys.argv[3]]
                addpop(vpn, pop)
            elif command == 'delpop':
                pop = topop(sys.argv[3])
                delpop(vpn, pop)
            elif command == 'addsite':
                site = tosite(sys.argv[3])
                addsite(vpn, site)
            elif command == 'delsite':
                site = tosite(sys.argv[3])
                delsite(vpn, site)
            elif command == 'addhost':
                host = tohost(sys.argv[3])
                addhost(vpn, host)
            elif command == 'delhost':
                host = tohost(sys.argv[3])
                if host == None:
                    return
                delhost(vpn, host)
            elif command == 'tapsite':
                site = tosite(sys.argv[3])
                tapsite(vpn, site)
            elif command == 'untapsite':
                site = tosite(sys.argv[3])
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
            elif command == 'save':
                confname = sys.argv[3]
                save(vpn, confname)
            elif command == 'visualize':
                confname = sys.argv[3]
                visualize(vpn, confname)
            else:
                print "unknown command"
                usage()
    except:
        #        print "Invalid arguments"
        #        usage()
        raise

if 'vpnIndex' not in globals() or vpnIndex == None:
    vpnIndex = {}
    globals()['vpnIndex'] = vpnIndex
if 'vpns' not in globals() or vpns == None:
    vpns = []
    globals()['vpns'] = vpns

if __name__ == '__main__':
    main()