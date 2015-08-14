"""
demo should be run first so that net, renderers, rendererIndex, vpns, vpnIndex
are available.
"""
from common.mac import MACAddress
from common.api import VPN
from mininet.mat import MAT
from mininet.utils import loadObject, saveObject
from mininet.l2vpn import SDNPopsIntent, SDNPopsRenderer

def usage():
    print "usage:"
    print "vpn sample $built-in_sample_index"
    print "vpn create $vpnname"
    print "vpn delete $vpnname"
    print "vpn kill $vpnname"
    print "vpn load $conf"
    print "vpn $vpnindex execute"
    print "vpn $vpnindex save $conf"
    print "vpn $vpnindex addpop $popindex"
    print "vpn $vpnindex delpop $popindex"
    print "vpn $vpnindex addsite $siteindex $lanVlan $siteVlan"
    print "vpn $vpnindex delsite $siteindex"
    print "vpn $vpnindex addhost $hostindex"
    print "vpn $vpnindex delhost $hostindex"
    print "vpn $vpnindex tapsite $siteindex"
    print "vpn $vpnindex untapsite $siteindex"
    print "vpn $vpnindex taphost $hostindex"
    print "vpn $vpnindex untaphost $hostindex"
    print "vpn $vpnindex tapmac $mac"
    print "vpn $vpnindex untapmac $mac"
    print "vpn $vpnindex settimeout $timeout"
    print "vpn $vpnindex visualize $conf"
    print "Note: vpnindex should not be any keyword such as sample, create, delete, kill, or load"
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
    return get(net.builder.pops, net.builder.popIndex, s)
def tosite(s):
    return get(net.builder.sites, net.builder.siteIndex, s)
def tohost(s):
    return get(net.builder.hosts, net.builder.hostIndex, s)

def sample(sampleindex):
    if sampleindex == '1':
        create('vpn1')
        vpn = tovpn('vpn1')
        addpop(vpn, topop('lbl'))
        addpop(vpn, topop('star'))
        addsite(vpn, tosite('lbl.gov'), 10, 11)
        addsite(vpn, tosite('anl.gov'), 10, 12)
        addhost(vpn, tohost('dtn-1@lbl.gov'))
        addhost(vpn, tohost('dtn-2@lbl.gov'))
        addhost(vpn, tohost('dtn-1@anl.gov'))
        execute(vpn)
    elif sampleindex == '2':
        create('vpn2')
        vpn = tovpn('vpn2')
        addpop(vpn, topop('lbl'))
        addpop(vpn, topop('cern'))
        addsite(vpn, tosite('lbl.gov'), 20, 21)
        addsite(vpn, tosite('cern.ch'), 20, 23)
        addsite(vpn, tosite('cern2.ch'), 20, 24)
        addhost(vpn, tohost('dtn-2@lbl.gov'))
        addhost(vpn, tohost('dtn-2@cern.ch'))
        addhost(vpn, tohost('dtn-2@cern2.ch'))
        execute(vpn)
    else:
        print "index %s is not implemented" % sampleindex

def addVpn(vpn):
    renderer = vpn.props['renderer']
    renderers.append(renderer)
    rendererIndex[renderer.name] = renderer
    vpns.append(vpn)
    vpnIndex[vpn.name] = vpn

def save(vpn, confname):
    obj = vpn.serialize()
    saveObject(obj, confname)

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
    for (site, hosts, lanVlan, siteVlan) in vpn.props['participants']:
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
    saveObject(obj, confname)

def load(confname):
    obj = loadObject(confname)
    vpn = VPN.deserialize(obj, net)
    for (sitename, hostnames, lanVlan, siteVlan) in obj['participants']:
        site = net.builder.siteIndex[sitename]
        siteRenderer = rendererIndex[sitename]
        siteRenderer.addVlan(lanVlan, siteVlan)
        for hostname in hostnames:
            siteRenderer.addHost(net.builder.hostIndex[hostname], lanVlan)
    addVpn(vpn)

def create(vpnname):
    if vpnname in vpnIndex:
        print "vpn %r exists already" % vpnname
        return

    vpn = VPN(vpnname)
    intent = SDNPopsIntent(name=vpn.name, vpn=vpn, wan=net.builder.wan)
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
    for (site, hosts, lanVlan, siteVlan) in vpn.props['participantIndex'].values():
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

def addsite(vpn, site, lanVlan, siteVlan):
    if lanVlan <= 0:
        print "siteVlan should be greater than 0"
        return
    if siteVlan <= 0:
        print "siteVlan should be greater than 0"
        return
    popsRenderer = rendererIndex[vpn.name]
    if not popsRenderer.addSite(site, siteVlan):
        print "something's wrong while adding the site."
        # possible issues: site.props['pop'] is not added into the VPN yet
        return
    if not vpn.addSite(site, lanVlan, siteVlan):
        print "something's wrong while adding the site."
        # possible issues: duplicated site
        return
    siteRenderer = rendererIndex[site.name]
    siteRenderer.addVlan(lanVlan, siteVlan)
    print "The site %s is added into VPN %s successfully" % (site.name, vpn.name)

def delsite(vpn, site):
    lanVlan = vpn.props['participantIndex'][site.name][2]
    siteVlan = vpn.props['participantIndex'][site.name][3]
    if not vpn.checkSite(site):
        print "site not found in the vpn"
        return
    siteRenderer = rendererIndex[site.name]
    siteRenderer.delVlan(lanVlan, siteVlan)
    popsRenderer = rendererIndex[vpn.name]
    popsRenderer.delSite(site)
    vpn.delSite(site)

def addhost(vpn, host):
    if not vpn.addHost(host):
        print "something wrong while adding the host; Please make sure that the site of the host joined the VPN."
        return
    sitename = host.props['site'].name
    siteRenderer = rendererIndex[sitename]
    siteRenderer.addHost(host, vpn.props['participantIndex'][sitename][2])
    print "The host %s is added into VPN %s successfully" % (host.name, vpn.name)

def delhost(vpn, host):
    if not vpn.delHost(host):
        print "something wrong while deleting the host; Please make sure that the host joined the VPN."
        return
    sitename = host.props['site'].name
    siteRenderer = rendererIndex[sitename]
    siteRenderer.delHost(host, vpn.props['participantIndex'][sitename][2])

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
    if not 'net' in globals():
        print 'Please run demo first'
        return
    try:
        command = sys.argv[1].lower()
        if command == 'sample':
            sampleindex = sys.argv[2]
            sample(sampleindex)
        elif command == 'create':
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
            elif command == 'addpop':
                pop = topop(sys.argv[3])
                addpop(vpn, pop)
            elif command == 'delpop':
                pop = topop(sys.argv[3])
                delpop(vpn, pop)
            elif command == 'addsite':
                site = tosite(sys.argv[3])
                lanVlan = toint(sys.argv[4])
                siteVlan = toint(sys.argv[5])
                addsite(vpn, site, lanVlan, siteVlan)
            elif command == 'delsite':
                site = tosite(sys.argv[3])
                delsite(vpn, site)
            elif command == 'addhost':
                host = tohost(sys.argv[3])
                addhost(vpn, host)
            elif command == 'delhost':
                host = tohost(sys.argv[3])
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
        print "Invalid arguments"
        usage()
if __name__ == '__main__':
    main()