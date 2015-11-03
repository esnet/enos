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
"""
demo should be run first so that net, renderers, rendererIndex, vpns, vpnIndex
are available.
"""
from layer2.common.mac import MACAddress
from layer2.common.api import VPN
from layer2.vpn.mat import MAT
from layer2.vpn.l2vpn import SDNPopsIntent, SDNPopsRenderer

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
    renderer = vpn.props['renderer']
    renderers.append(renderer)
    rendererIndex[renderer.name] = renderer
    vpns.append(vpn)
    vpnIndex[vpn.name] = vpn

def save(vpn, confname):
    obj = vpn.serialize()

def getNode(node, nodeIndex):
    if node.name in nodeIndex:
        return nodeIndex[node.name]
    nodeIndex[node.name] = {'name':node.name, 'info':[]}
    return nodeIndex[node.name]
def linkname(node1, node2):
    if node1.name <= node2.name:
        return node1.name + ":" + node2.name
    else:
        return node2.name + ":" + node1.name
def getLink(node1, node2, linkIndex):
    name = linkname(node1, node2)
    if name in linkIndex:
        return linkIndex[name]
    linkIndex[name] = {'name':name, 'endpoint1':node1.name, 'endpoint2':node2.name, 'info':[]}
    return linkIndex[name]
def visualize(vpn, confname):
    obj = {}
    nodeIndex = {}
    linkIndex = {}
    pops = []
    for (site, hosts, siteVlan) in vpn.props['participants']:
        siteRouter = site.props['siteRouter']
        getNode(siteRouter, nodeIndex)['info'].append({'type':'text', 'attr':'role', 'value':"Site Router"})
        for host in hosts:
            getNode(host, nodeIndex)['info'].append({'type':'text', 'attr':'role', 'value':"End User"})
            getLink(host, siteRouter, linkIndex)['info'].append({'type':'text','attr':'vlan','value':lanVlan})
        pop = site.props['pop']
        if not pop in pops:
            coreRouter = pop.props['coreRouter']
            getNode(coreRouter, nodeIndex)['info'].append({'type':'text', 'attr':'role', 'value':"Core Router"})
            getLink(coreRouter, siteRouter, linkIndex)['info'].append({'type':'text','attr':'vlan','value':siteVlan})
            hwSwitch = pop.props['hwSwitch']
            getNode(hwSwitch, nodeIndex)['info'].append({'type':'text', 'attr':'role', 'value':"Hardware Switch"})
            port = hwSwitch.props['sitePortIndex'][site.name]
            getLink(coreRouter, hwSwitch, linkIndex)['info'].append({'type':'text','attr':'vlan','value':siteVlan})
            swSwitch = pop.props['swSwitch']
            getNode(swSwitch, nodeIndex)['info'].append({'type':'text', 'attr':'role', 'value':"Software Switch"})
            getLink(swSwitch, hwSwitch, linkIndex)['info'].append({'type':'text','attr':'vlan','value':siteVlan})
            serviceVm = pop.props['serviceVm']
            getNode(serviceVm, nodeIndex)['info'].append({'type':'text', 'attr':'role', 'value':"Service Virtual Machine"})
            getLink(swSwitch, serviceVm, linkIndex)['info'].append({'type':'text','attr':'vlan','value':siteVlan})
            renderer = vpn.props['renderer']
            hwScope = renderer.props['scopeIndex'][hwSwitch.name]
            for flowmod in hwScope.props['flowmodIndex'].values():
                getNode(hwSwitch, nodeIndex)['info'].append({'type':'text', 'attr':'flowmod', 'value':flowmod.visualize()})
            swScope = renderer.props['scopeIndex'][swSwitch.name]
            for flowmod in swScope.props['flowmodIndex'].values():
                getNode(swSwitch, nodeIndex)['info'].append({'type':'text', 'attr':'flowmod', 'value':flowmod.visualize()})
            for otherPop in pops:
                vlan = coreRouter.props['wanPortIndex'][otherPop.name].props['links'][0].props['vlan']

                otherCoreRouter = otherPop.props['coreRouter']
                otherHwSwitch = otherPop.props['hwSwitch']
                otherSwSwitch = otherPop.props['swSwitch']
                otherServiceVm = otherPop.props['serviceVm']

                getLink(coreRouter, otherCoreRouter, linkIndex)['info'].append({'type':'text','attr':'vlan','value':vlan})
                # pop
                getLink(coreRouter, hwSwitch, linkIndex)['info'].append({'type':'text','attr':'vlan','value':vlan})
                getLink(swSwitch, hwSwitch, linkIndex)['info'].append({'type':'text','attr':'vlan','value':vlan})
                getLink(swSwitch, serviceVm, linkIndex)['info'].append({'type':'text','attr':'vlan','value':vlan})
                # other pop
                getLink(otherCoreRouter, otherHwSwitch, linkIndex)['info'].append({'type':'text','attr':'vlan','value':vlan})
                getLink(otherSwSwitch, otherHwSwitch, linkIndex)['info'].append({'type':'text','attr':'vlan','value':vlan})
                getLink(otherSwSwitch, otherServiceVm, linkIndex)['info'].append({'type':'text','attr':'vlan','value':vlan})
            pops.append(pop)

    nodes = []
    for node in nodeIndex.values():
        nodes.append(node)
    links = []
    for link in linkIndex.values():
        links.append(link)
    obj['nodes'] = nodes
    obj['links'] = links

def load(confname):
    print "Not implemented yet"

def create(vpnname):
    if vpnname in vpnIndex:
        print "vpn %r exists already" % vpnname
        return
    vpn = VPN(vpnname)
    intent = SDNPopsIntent(name=vpn.name, vpn=vpn, wan=topo.builder.wan)
    renderer = SDNPopsRenderer(intent)
    renderer.execute() # no function since no scope yet
    vpn.props['renderer'] = renderer
    vpn.props['mat'] = MAT(vpn.props['vid'])
    addVpn(vpn)
    print "VPN %s is created successfully." % vpn.name

def delete(vpnname):
    if not vpnname in vpnIndex:
        print "vpn name %s not found" % vpnname
        return
    vpn = vpnIndex[vpnname]
    renderer = vpn.props['renderer']
    if not renderer.clean():
        print "Something's wrong while deleting the VPN. Please make sure all pop is deleted in the VPN"
        return
    vpnIndex.pop(vpn.name)
    vpns.remove(vpn)
    rendererIndex.pop(renderer.name)
    renderers.remove(renderer)

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
    popsRenderer = rendererIndex[vpn.name]
    if not popsRenderer.addPop(pop):
        print "something's wrong while adding the pop."
        # possible issues: duplicated pop
        return
    print "Pop %s is added into VPN %s successfully." % (pop.name, vpn.name)

def delpop(vpn, pop):
    popsRenderer = rendererIndex[vpn.name]
    if not popsRenderer.delPop(pop):
        print "something's wrong while deleting the pop."
        # possible issues: pop not empty
        return

def addsite(vpn, site):
    if not 'SiteToCore' in site.props:
        print "site is not connected to the testbed"
        return
    link = site.props['SiteToCore']
    popsRenderer = rendererIndex[vpn.name]
    if not popsRenderer.addSite(site, link):
        print "something's wrong while adding the site."
        # possible issues: site.props['pop'] is not added into the VPN yet
        return
    if not vpn.addSite(site, link):
        print "something's wrong while adding the site."
        # possible issues: duplicated site
        return
    print "The site %s is added into VPN %s successfully" % (site.name, vpn.name)

def delsite(vpn, site):
    siteVlan = vpn.props['participantIndex'][site.name][2]
    if not vpn.checkSite(site):
        print "site not found in the vpn"
        return
#    siteRenderer = rendererIndex[site.name]
#    siteRenderer.delVlan(siteVlan)
    popsRenderer = rendererIndex[vpn.name]
    popsRenderer.delSite(site)
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
if __name__ == '__main__':
    main()