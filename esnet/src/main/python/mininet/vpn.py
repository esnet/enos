"""
demo should be run first so that net, renderers, rendererIndex, vpns, vpnIndex
are available.
"""
from common.api import VPN
from mininet.l2vpn import SDNPopsIntent, SDNPopsRenderer

def usage():
    print "usage:"
    print "vpn sample built-in_sample_index"
    print "vpn create vpnname vid lanVlan"
    print "vpn vpnindex addsite siteindex wanVlan"
    print "vpn vpnindex addhost hostindex"
    print "vpn vpnindex execute"
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
        index = '0'
    else:
        index = args[0]
    if index == '0':
        create(['vpn1', '1234', '10'])
        addsite(['vpn1', 'addsite', '0', '11']) # lbl.gov
        addsite(['vpn1', 'addsite', '1', '12']) # anl.gov
        addhost(['vpn1', 'addhost', '0']) # dtn-1@lbl.gov
        addhost(['vpn1', 'addhost', '2']) # dtn-1@anl.gov
        execute(['vpn1', 'execute'])
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
    sitename = host.props['connectTo'].name # siteRouter's name == site's name
    siteRenderer = rendererIndex[sitename]
    siteRenderer.addHost(host, vpn.props['lanVlan'], vpn.props['participantIndex'][sitename][2])
def execute(args):
    # args = [vpnindex, 'execute']
    vpnindex = args[0]
    vpn = get(vpns, vpnIndex, vpnindex)
    vpn.props['renderer'].execute()
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
    elif len(command_args) < 4:
        usage()
    elif command_args[3] == 'addsite':
        addsite(command_args[2:])
    elif command_args[3] == 'addhost':
        addhost(command_args[2:])
    elif command_args[3] == 'execute':
        execute(command_args[2:])
    else:
        print "unknown command"
        usage()
if __name__ == '__main__':
    main()