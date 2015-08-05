"""
demo should be run first so that net, renderers, rendererIndex, vpns, vpnIndex
are available.
"""
from common.mac import MACAddress
from common.api import VPN
from mininet.utils import loadObject, saveObject
from mininet.l2vpn import SDNPopsIntent, SDNPopsRenderer

def usage():
    print "usage:"
    print "vpn sample $built-in_sample_index"
    print "vpn $vpnindex execute"
    print "vpn create $vpnname $vid $lanVlan"
    print "vpn delete $vpnname"
    print "vpn kill $vpnname"
    print "vpn load $conf"
    print "vpn $vpnindex save $conf"
    print "vpn $vpnindex addpop $popindex"
    print "vpn $vpnindex delpop $popindex"
    print "vpn $vpnindex addsite $siteindex $wanVlan"
    print "vpn $vpnindex delsite $siteindex"
    print "vpn $vpnindex addhost $hostindex [$cheating]"
    print "vpn $vpnindex delhost $hostindex"
    print "vpn $vpnindex tapsite $siteindex"
    print "vpn $vpnindex untapsite $siteindex"
    print "vpn $vpnindex taphost $hostindex"
    print "vpn $vpnindex untaphost $hostindex"
    print "vpn $vpnindex tapmac $mac"
    print "vpn $vpnindex untapmac $mac"
def toint(s):
    try:
        return int(s)
    except:
        return -1
def tobool(s):
    return s.lower() in ('yes', 'true', '1', 't')
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
        print "%r not found" % index
        usage()
        sys.exit()

def sample(args):
    if len(args) < 1:
        index = '1'
    else:
        index = args[0]
    if index == '1':
        create(['vpn1', '1234', '10'])
        addpop(['vpn1', 'addpop', 'lbl'])
        addpop(['vpn1', 'addpop', 'star'])
        addsite(['vpn1', 'addsite', 'lbl.gov', '11'])
        addsite(['vpn1', 'addsite', 'anl.gov', '12'])
        addhost(['vpn1', 'addhost', 'dtn-1@lbl.gov', 'False'])
        addhost(['vpn1', 'addhost', 'dtn-2@lbl.gov', 'False'])
        addhost(['vpn1', 'addhost', 'dtn-1@anl.gov', 'False'])
        execute(['vpn1', 'execute'])
    elif index == '2':
        create(['vpn2', '5678', '20'])
        addpop(['vpn2', 'addpop', 'lbl'])
        addpop(['vpn2', 'addpop', 'cern'])
        addsite(['vpn2', 'addsite', 'lbl.gov', '21'])
        addsite(['vpn2', 'addsite', 'cern.ch', '23'])
        addsite(['vpn2', 'addsite', 'cern2.ch', '24'])
        addhost(['vpn2', 'addhost', 'dtn-2@lbl.gov'])
        addhost(['vpn2', 'addhost', 'dtn-2@cern.ch'])
        addhost(['vpn2', 'addhost', 'dtn-2@cern2.ch'])
        execute(['vpn2', 'execute'])
    else:
        print "index %s is not implemented" % index

def addVpn(vpn):
    renderer = vpn.props['renderer']
    renderers.append(renderer)
    rendererIndex[renderer.name] = renderer
    vpns.append(vpn)
    vpnIndex[vpn.name] = vpn

def save(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # vpn vpnindex save confname
    (vpnindex, confname) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    obj = vpn.serialize()
    saveObject(obj, confname)

def load(args):
    if len(args) < 1:
        print "invalid arguments."
        usage()
        return
    confname = args[0]
    obj = loadObject(confname)
    vpn = VPN.deserialize(obj, net)
    lanVlan = vpn.props['lanVlan']
    for (sitename, hostnames, siteVlan) in obj['participants']:
        site = net.builder.siteIndex[sitename]
        siteRenderer = rendererIndex[sitename]
        siteRenderer.addVlan(lanVlan, siteVlan)
        for hostname in hostnames:
            siteRenderer.addHost(net.builder.hostIndex[hostname], lanVlan)
    addVpn(vpn)

def create(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    (vpnname, vid, lanVlan) = [args[0], toint(args[1]), toint(args[2])]
    if vid < 1 or vid >= 2**24:
        print "vid should be in the range 1 to 2^24"
        return
    if lanVlan < 0:
        print "lanVlan should be greater or equal than 0"
        return

    if vpnname in vpnIndex:
        print "vpn %r exists already" % vpnname
        return

    if filter(lambda vpn : vpn.props['vid'] == vid, vpns):
        print "vid %r exists already" % vid
        return

    vpn = VPN(vpnname, vid, lanVlan)
    intent = SDNPopsIntent(name=vpn.name, vpn=vpn, wan=net.builder.wan)
    renderer = SDNPopsRenderer(intent)
    renderer.execute() # no function since no scope yet
    vpn.props['renderer'] = renderer
    vpn.props['mat'] = MAT(vpn.props['vid'])
    addVpn(vpn)
    print "VPN %s is created successfully." % vpn.name

def delete(args):
    if len(args) < 1:
        print "invalid arguments."
        usage()
        return
    vpnname = args[0]
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

def kill(args):
    if len(args) < 1:
        print "invalid arguments."
        usage()
        return
    vpnname = args[0]
    if not vpnname in vpnIndex:
        print "vpn name %s not found" % vpnname
        return
    vpn = vpnIndex[vpnname]
    for (site, hosts, siteVlan) in vpn.props['participantIndex'].values():
        for host in hosts:
            delhost([vpn.name, 'delhost', host.name])
        delsite([vpn.name, 'delsite', site.name])
    renderer = vpn.props['renderer']
    for pop in renderer.props['popIndex'].values():
        delpop([vpn.name, 'delpop', pop.name])
    delete([vpn.name])

def execute(args):
    if len(args) < 2:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'execute']
    vpnindex = args[0]
    vpn = get(vpns, vpnIndex, vpnindex)
    vpn.props['renderer'].execute()

def addpop(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'addpop', popindex]
    (vpnindex, popindex) = [args[0], args[2]]

    vpn = get(vpns, vpnIndex, vpnindex)
    pop = get(net.builder.pops, net.builder.popIndex, popindex)
    popsRenderer = rendererIndex[vpn.name]
    if not popsRenderer.addPop(pop):
        print "something's wrong while adding the pop."
        # possible issues: duplicated pop
        return
    print "Pop %s is added into VPN %s successfully." % (pop.name, vpn.name)

def delpop(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'delpop', popindex]
    (vpnindex, popindex) = [args[0], args[2]]

    vpn = get(vpns, vpnIndex, vpnindex)
    pop = get(net.builder.pops, net.builder.popIndex, popindex)
    popsRenderer = rendererIndex[vpn.name]
    if not popsRenderer.delPop(pop):
        print "something's wrong while deleting the pop."
        # possible issues: pop not empty
        return

def addsite(args):
    if len(args) < 4:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'addsite', siteindex, siteVlan]
    (vpnindex, siteindex, siteVlan) = [args[0], args[2], toint(args[3])]

    if siteVlan < 0:
        print "siteVlan should be greater or equal than 0"
        return
    vpn = get(vpns, vpnIndex, vpnindex)
    site = get(net.builder.sites, net.builder.siteIndex, siteindex)
    popsRenderer = rendererIndex[vpn.name]
    if not popsRenderer.addSite(site, siteVlan):
        print "something's wrong while adding the site."
        # possible issues: site.props['pop'] is not added into the VPN yet
        return
    if not vpn.addSite(site, siteVlan):
        print "something's wrong while adding the site."
        # possible issues: duplicated site
        return
    siteRenderer = rendererIndex[site.name]
    siteRenderer.addVlan(vpn.props['lanVlan'], siteVlan)
    print "The site %s is added into VPN %s successfully" % (site.name, vpn.name)

def delsite(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'delsite', siteindex]
    (vpnindex, siteindex) = [args[0], args[2]]

    vpn = get(vpns, vpnIndex, vpnindex)
    site = get(net.builder.sites, net.builder.siteIndex, siteindex)
    siteVlan = vpn.props['participantIndex'][site.name][2]
    if not vpn.checkSite(site):
        print "site not found in the vpn"
        return
    siteRenderer = rendererIndex[site.name]
    siteRenderer.delVlan(vpn.props['lanVlan'], siteVlan)
    popsRenderer = rendererIndex[vpn.name]
    popsRenderer.delSite(site)
    vpn.delSite(site)

def addhost(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'addhost', hostindex, cheating(optional)]
    (vpnindex, hostindex) = [args[0], args[2]]
    cheating = False
    if len(args) >= 4:
        cheating = tobool(args[3])
    vpn = get(vpns, vpnIndex, vpnindex)
    host = get(net.builder.hosts, net.builder.hostIndex, hostindex)
    if not vpn.addHost(host, cheating):
        print "something wrong while adding the host; Please make sure that the site of the host joined the VPN."
        return
    sitename = host.props['site'].name
    siteRenderer = rendererIndex[sitename]
    siteRenderer.addHost(host, vpn.props['lanVlan'])
    print "The host %s is added into VPN %s successfully" % (host.name, vpn.name)

def delhost(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'delhost', hostindex]
    (vpnindex, hostindex) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    host = get(net.builder.hosts, net.builder.hostIndex, hostindex)
    if not vpn.delHost(host):
        print "something wrong while deleting the host; Please make sure that the host joined the VPN."
        return
    sitename = host.props['site'].name
    siteRenderer = rendererIndex[sitename]
    siteRenderer.delHost(host, vpn.props['lanVlan'])

def tapsite(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'tapsite', siteindex]
    (vpnindex, siteindex) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    site = get(net.builder.sites, net.builder.siteIndex, siteindex)
    vpn.props['renderer'].tapSite(site)

def untapsite(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'untapsite', siteindex]
    (vpnindex, siteindex) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    site = get(net.builder.sites, net.builder.siteIndex, siteindex)
    vpn.props['renderer'].untapSite(site)

def taphost(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'taphost', hostindex]
    (vpnindex, hostindex) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    host = get(net.builder.hosts, net.builder.hostIndex, hostindex)
    vpn.props['renderer'].tapHost(host)

def untaphost(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'untaphost', hostindex]
    (vpnindex, hostindex) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    host = get(net.builder.hosts, net.builder.hostIndex, hostindex)
    vpn.props['renderer'].untapHost(host)

def tapmac(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'tapmac', mac]
    (vpnindex, mac) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    try:
        m = MACAddress(int(mac))
    except:
        try:
            m = MACAddress(mac)
        except:
            print "invalid mac"
            return
    vpn.props['renderer'].tapMacCLI(m)

def untapmac(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'untapmac', mac]
    (vpnindex, mac) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    try:
        m = MACAddress(int(mac))
    except:
        try:
            m = MACAddress(mac)
        except:
            print "invalid mac"
            return
    vpn.props['renderer'].untapMac(m)

def main():
    if not 'net' in globals():
        print 'Please run demo first'
        return

    if len(command_args) < 3:
        usage()
        return

    if command_args[2] == 'sample':
        sample(command_args[3:])
    elif command_args[2] == 'create':
        create(command_args[3:])
    elif command_args[2] == 'delete':
        delete(command_args[3:])
    elif command_args[2] == 'kill':
        kill(command_args[3:])
    elif command_args[2] == 'execute':
        execute(command_args[3:])
    elif command_args[2] == 'load':
        load(command_args[3:])
    elif len(command_args) < 4:
        usage()
    elif command_args[3] == 'addpop':
        addpop(command_args[2:])
    elif command_args[3] == 'delpop':
        delpop(command_args[2:])
    elif command_args[3] == 'addsite':
        addsite(command_args[2:])
    elif command_args[3] == 'delsite':
        delsite(command_args[2:])
    elif command_args[3] == 'addhost':
        addhost(command_args[2:])
    elif command_args[3] == 'delhost':
        delhost(command_args[2:])
    elif command_args[3] == 'tapsite':
        tapsite(command_args[2:])
    elif command_args[3] == 'untapsite':
        untapsite(command_args[2:])
    elif command_args[3] == 'taphost':
        taphost(command_args[2:])
    elif command_args[3] == 'untaphost':
        untaphost(command_args[2:])
    elif command_args[3] == 'tapmac':
        tapmac(command_args[2:])
    elif command_args[3] == 'untapmac':
        untapmac(command_args[2:])
    elif command_args[3] == 'save':
        save(command_args[2:])
    else:
        print "unknown command"
        usage()
if __name__ == '__main__':
    main()