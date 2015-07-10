
def usage():
    print "usage:"
    print "list flowmods: list names of all flowmods"
    print "list hosts: list names of all hosts"
    print "list host $INDEX: list the host (index could be number or name)"
    print "list links: list names of all links"
    print "list link $INDEX: list the link (index could be number or name)"
    print "list pops: list names of all pops"
    print "list pop $INDEX: list the pop (index could be number or name)"
    print "list ports: list names of all ports"
    print "list port $INDEX: list the port (index could be number or name)"
    print "list scopes: list names of all scopes"
    print "list scope $INDEX: list the scope (index could be number or name)"
    print "list sites: list names of all sites"
    print "list site $INDEX: list the site (index could be number or name)"
    print "list switches: list names of all switches"
    print "list switch $INDEX: list the switch (index could be number or name)"
    print "list vpns: list names of all vpns"
    print "list vpn $INDEX: list the vpn (index could be number or name)"
    print "list wan: list the wan"

def showlist(l):
    for i in range(len(l)):
        print "[%d] %r" % (i, l[i].name)
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
def showobj(obj):
    print obj
    if obj and obj.props:
        for prop in obj.props.items():
            print "%s: %r" % (prop[0], prop[1])

def main():
    if not 'net' in globals():
        print "Please run demo first"
        return
    if len(command_args) < 3:
        usage()
    elif command_args[2] == 'flowmods':
        i = 0
        for renderer in renderers:
            for key in renderer.flowmodIndex.keys():
                print "[%d] %s" % (i, key)
                i += 1
    elif command_args[2] == 'hosts':
        showlist(net.builder.hosts)
    elif command_args[2] == 'links':
        showlist(net.builder.links)
    elif command_args[2] == 'pops':
        showlist(net.builder.pops)
    elif command_args[2] == 'ports':
        ports = []
        for switch in net.builder.switches:
            ports.extend(switch.props['ports'].values())
        # not interested in ports on host
        showlist(ports)
    elif command_args[2] == 'renderers':
        showlist(renderers)
    elif command_args[2] == 'scopes':
        showlist(net.controller.scopes.values())
    elif command_args[2] == 'sites':
        showlist(net.builder.sites)
    elif command_args[2] == 'switches':
        showlist(net.builder.switches)
    elif command_args[2] == 'vpns':
        showlist(vpns)
    elif command_args[2] == 'wan':
        showobj(net.builder.wan)
    elif len(command_args) < 4:
        usage()
    elif command_args[2] == 'host':
        host = get(net.builder.hosts, net.builder.hostIndex, command_args[3])
        showobj(host)
    elif command_args[2] == 'link':
        link = get(net.builder.links, net.builder.linkIndex, command_args[3])
        showobj(link)
    elif command_args[2] == 'pop':
        pop = get(net.builder.pops, net.builder.popIndex, command_args[3])
        showobj(pop)
    elif command_args[2] == 'port':
        ports = []
        for switch in net.builder.switches:
            ports.extend(switch.props['ports'].values())
        portIndex = {}
        for port in ports:
            portIndex[port.name] = port
        port = get(ports, portIndex, command_args[3])
        showobj(port)
    elif command_args[2] == 'renderer':
        renderer = get(renderers, rendererIndex, command_args[3])
        showobj(renderer)
    elif command_args[2] == 'scope':
        scopeIndex = {}
        for scope in net.controller.scopes.values():
            scopeIndex[scope.name] = scope
        scope = get(net.controller.scopes.values(), scopeIndex, command_args[3])
        showobj(scope)
    elif command_args[2] == 'site':
        site = get(net.builder.sites, net.builder.siteIndex, command_args[3])
        showobj(site)
    elif command_args[2] == 'switch':
        switch = get(net.builder.switches, net.builder.switchIndex, command_args[3])
        showobj(switch)
    elif command_args[2] == 'vpn':
        vpn = get(vpns, vpnIndex, command_args[3])
        showobj(vpn)

if __name__ == '__main__':
    main()