"""
demo should be run first so that net, renderers, rendererIndex, vpns, vpnIndex
are available.
"""
from common.api import VPN
from mininet.l2vpn import SDNPopsIntent, SDNPopsRenderer

def usage():
    print "usage:"
    print "vpn sample $built-in_sample_index"
    print "vpn $vpnindex execute"
    print "vpn create $vpnname $vid $lanVlan"
    print "vpn $vpnindex addsite $siteindex $wanVlan"
    print "vpn $vpnindex addhost $hostindex"
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
        addsite(['vpn1', 'addsite', 'lbl.gov', '11'])
        addsite(['vpn1', 'addsite', 'anl.gov', '12'])
        addhost(['vpn1', 'addhost', 'dtn-1@lbl.gov'])
        addhost(['vpn1', 'addhost', 'dtn-2@lbl.gov'])
        addhost(['vpn1', 'addhost', 'dtn-1@anl.gov'])
        execute(['vpn1', 'execute'])
    elif index == '2':
        create(['vpn2', '5678', '20'])
        addsite(['vpn2', 'addsite', 'lbl.gov', '21'])
        addsite(['vpn2', 'addsite', 'anl.gov', '22'])
        addsite(['vpn2', 'addsite', 'cern.ch', '23'])
        addhost(['vpn2', 'addhost', 'dtn-2@lbl.gov'])
        addhost(['vpn2', 'addhost', 'dtn-2@anl.gov'])
        addhost(['vpn2', 'addhost', 'dtn-2@cern.ch'])
        execute(['vpn2', 'execute'])
    else:
        print "index %s is not implemented" % index
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
    renderer.execute() # no function since no scope
    vpn.props['renderer'] = renderer
    vpn.props['mat'] = MAT(vpn.props['vid'])

    renderers.append(renderer)
    rendererIndex[renderer.name] = renderer
    vpns.append(vpn)
    vpnIndex[vpn.name] = vpn

def execute(args):
    if len(args) < 2:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'execute']
    vpnindex = args[0]
    vpn = get(vpns, vpnIndex, vpnindex)
    vpn.props['renderer'].execute()

def addsite(args):
    if len(args) < 4:
        print "invalid arguments."
        usage()
        return
    (vpnindex, siteindex, wanVlan) = [args[0], args[2], toint(args[3])]

    if wanVlan < 0:
        print "wanVlan should be greater or equal than 0"
        return
    vpn = get(vpns, vpnIndex, vpnindex)
    site = get(net.builder.sites, net.builder.siteIndex, siteindex)
    (serviceVm, link) = vpn.addSite(site, wanVlan)
    net.builder.addHost(serviceVm)
    net.builder.addLink(link)
    net.buildHost(serviceVm)
    net.buildLink(link)
    siteRenderer = rendererIndex[site.name]
    siteRenderer.addVlan(vpn.props['lanVlan'], wanVlan)
    popsRenderer = rendererIndex[vpn.name]
    popsRenderer.addSite(site, wanVlan)

def addhost(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    (vpnindex, hostindex) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    host = get(net.builder.hosts, net.builder.hostIndex, hostindex)
    vpn.addHost(host)
    sitename = host.props['site'].name
    siteRenderer = rendererIndex[sitename]
    siteRenderer.addHost(host, vpn.props['lanVlan'])

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
        m = MACAddress(mac)
    except:
        try:
            m = MACAddress(int(mac))
        except:
            print "invalid mac"
            return
    vpn.props['renderer'].tapMac(m)

def untapmac(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'untapmac', mac]
    (vpnindex, mac) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    try:
        m = MACAddress(mac)
    except:
        try:
            m = MACAddress(int(mac))
        except:
            print "invalid mac"
            return
    vpn.props['renderer'].untapMac(m)

def main():
    if not net:
        print 'Please run demo first'
        return

    if len(command_args) < 3:
        usage()
        return

    if command_args[2] == 'sample':
        sample(command_args[3:])
    elif command_args[2] == 'create':
        create(command_args[3:])
    elif command_args[2] == 'execute':
        execute(command_args[3:])
    elif len(command_args) < 4:
        usage()
    elif command_args[3] == 'addsite':
        addsite(command_args[2:])
    elif command_args[3] == 'addhost':
        addhost(command_args[2:])
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
    else:
        print "unknown command"
        usage()
if __name__ == '__main__':
    main()