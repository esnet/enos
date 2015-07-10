from common.intent import Expectation
from common.intent import Intent

def usage():
    print "usage:"
    print "list expectations: list names of all expectations"
    print "list expecatation $INDEX: list a single expectation (by name)"
    print "list hosts: list names of all hosts"
    print "list host $INDEX: list the host (index could be number or name)"
    print "list intents: list names of all intents"
    print "list intent $INDEX: list a single intent (by name)"
    print "list links: list names of all links"
    print "list link $INDEX: list the link (index could be number or name)"
    print "list pops: list names of all pops"
    print "list pop $INDEX: list the pop (index could be number or name)"
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
    if not net:
        print "Please run demo first"
        return
    if len(command_args) < 3:
        usage()
    elif command_args[2] == 'expectations':
        for i in sorted(Expectation.directory):
            print i
    elif command_args[2] == 'hosts':
        showlist(net.builder.hosts)
    elif command_args[2] == 'intents':
        for i in sorted(Intent.directory):
            print i
    elif command_args[2] == 'links':
        showlist(net.builder.links)
    elif command_args[2] == 'pops':
        showlist(net.builder.pops)
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
    elif command_args[2] == 'expectation':
        expectation = get(None, Expectation.directory, command_args[3])
        showobj(expectation)
    elif command_args[2] == 'host':
        host = get(net.builder.hosts, net.builder.hostIndex, command_args[3])
        showobj(host)
    elif command_args[2] == 'intent':
        intent = get(None, Intent.directory, command_args[3])
        showobj(intent)
    elif command_args[2] == 'link':
        link = get(net.builder.links, net.builder.linkIndex, command_args[3])
        showobj(link)
    elif command_args[2] == 'pop':
        pop = get(net.builder.pops, net.builder.popIndex, command_args[3])
        showobj(pop)
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