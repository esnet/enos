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
    print "vpn vpnindex tap siteindex"
    print "vpn vpnindex untap siteindex"
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
        create(['vpn1', '1234', '10']) # vid=1234, lanVlan=10
        addsite(['vpn1', 'addsite', 'lbl.gov', '11']) # wanVlan=11
        addsite(['vpn1', 'addsite', 'anl.gov', '12'])
        addsite(['vpn1', 'addsite', 'cern.ch', '13'])
        addhost(['vpn1', 'addhost', 'dtn-1@lbl.gov'])
        addhost(['vpn1', 'addhost', 'dtn-2@lbl.gov'])
        addhost(['vpn1', 'addhost', 'dtn-1@anl.gov'])
        addhost(['vpn1', 'addhost', 'dtn-2@anl.gov'])
        addhost(['vpn1', 'addhost', 'dtn-1@cern.ch'])
        addhost(['vpn1', 'addhost', 'dtn-2@cern.ch'])
        execute(['vpn1', 'execute'])
        print "Reminder: you should add serviceVms on Mininet manually"
        print "mininet> px net.addVm('vpn1','lbl')"
        print "mininet> px net.addVm('vpn1','star')"
        print "mininet> px net.addVm('vpn1','cern')"
        print "mininet> switch s6 start"
        print "mininet> switch s18 start"
        print "mininet> switch s21 start"

    elif index == '2':
        create(['vpn2', '5678', '20'])
        addsite(['vpn2', 'addsite', 'lbl.gov', '21'])
        addsite(['vpn2', 'addsite', 'anl.gov', '22'])
        addhost(['vpn2', 'addhost', 'dtn-1@lbl.gov'])
        addhost(['vpn2', 'addhost', 'dtn-1@anl.gov'])
        execute(['vpn2', 'execute'])
        print "Reminder: you should add serviceVms on Mininet manually"
        print "mininet> px net.addVm('vpn2','lbl')"
        print "mininet> px net.addVm('vpn2','star')"
        print "mininet> switch s6 start"
        print "mininet> switch s18 start"
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
def tap(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'tap', siteindex]
    (vpnindex, siteindex) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    site = get(net.builder.sites, net.builder.siteIndex, siteindex)
    vpn.props['renderer'].tap(site=site)
def untap(args):
    if len(args) < 3:
        print "invalid arguments."
        usage()
        return
    # args = [vpnindex, 'untap', siteindex]
    (vpnindex, siteindex) = [args[0], args[2]]
    vpn = get(vpns, vpnIndex, vpnindex)
    site = get(net.builder.sites, net.builder.siteIndex, siteindex)
    vpn.props['renderer'].untap(site=site)
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
    elif command_args[3] == 'tap':
        tap(command_args[2:])
    elif command_args[3] == 'untap':
        untap(command_args[2:])
    else:
        print "unknown command"
        usage()
if __name__ == '__main__':
    main()