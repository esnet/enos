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
from common.intent import Expectation
from common.intent import Intent

def usage():
    print "usage:"
    print "list entries: list names of all flow entries"
    print "list entry $INDEX: list the entry (index could be number or name)"
    print "list expectations: list names of all expectations"
    print "list expectation $INDEX: list a single expectation (by name)"
    print "list flowmods: list names of all flowmods"
    print "list hosts: list names of all hosts"
    print "list host $INDEX: list the host (index could be number or name)"
    print "list intents: list names of all intents"
    print "list intent $INDEX: list a single intent (by name)"
    print "list links: list names of all links"
    print "list link $INDEX: list the link (index could be number or name)"
    print "list pops: list names of all pops"
    print "list pop $INDEX: list the pop (index could be number or name)"
    print "list ports: list names of all ports"
    print "list port $INDEX: list the port (index could be number or name)"
    print "list renderers: list names of all rendererers"
    print "list renderer $INDEX: list a single renderer"
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
    if len(sys.argv) < 2:
        usage()
    else:
        command = sys.argv[1].lower()
        if command == 'entries':
            i = 0
            for vpn in vpns:
                for status in vpn.props['renderer'].props['statusIndex'].values():
                    print "[%d] %r" % (i, status.props['flowEntry'])
                    i += 1
        elif command == 'expectations':
            for i in sorted(Expectation.directory):
                print i
        elif command == 'flowmods':
            i = 0
            for renderer in renderers:
                for scope in renderer.props['scopeIndex'].values():
                    for flowmod in scope.props['flowmodIndex'].values():
                        print "[%d] %r" % (i, flowmod)
                        i += 1
        elif command == 'hosts':
            showlist(net.builder.hosts)
        elif command == 'intents':
            for i in sorted(Intent.directory):
                print i
        elif command == 'links':
            showlist(net.builder.links)
        elif command == 'pops':
            showlist(net.builder.pops)
        elif command == 'ports':
            showlist(net.builder.ports)
        elif command == 'renderers':
            showlist(renderers)
        elif command == 'scopes':
            showlist(net.controller.scopes.values())
        elif command == 'sites':
            showlist(net.builder.sites)
        elif command == 'switches':
            showlist(net.builder.switches)
        elif command == 'vpns':
            showlist(vpns)
        elif command == 'wan':
            showobj(net.builder.wan)
        elif len(sys.argv) < 3:
            usage()
        elif command == 'entry':
            entries = []
            i = 0
            for vpn in vpns:
                for status in vpn.props['renderer'].props['statusIndex'].values():
                    entries.append(status)
            status = get(entries, {}, sys.argv[2])
            showobj(status)
        elif command == 'expectation':
            expectation = get(None, Expectation.directory, sys.argv[2])
            showobj(expectation)
        elif command == 'host':
            host = get(net.builder.hosts, net.builder.hostIndex, sys.argv[2])
            showobj(host)
        elif command == 'intent':
            intent = get(None, Intent.directory, sys.argv[2])
            showobj(intent)
        elif command == 'link':
            link = get(net.builder.links, net.builder.linkIndex, sys.argv[2])
            showobj(link)
        elif command == 'pop':
            pop = get(net.builder.pops, net.builder.popIndex, sys.argv[2])
            showobj(pop)
        elif command == 'port':
            port = get(net.builder.ports, net.builder.portIndex, sys.argv[2])
            showobj(port)
        elif command == 'renderer':
            renderer = get(renderers, rendererIndex, sys.argv[2])
            showobj(renderer)
        elif command == 'scope':
            scopeIndex = {}
            for scope in net.controller.scopes.values():
                scopeIndex[scope.name] = scope
            scope = get(net.controller.scopes.values(), scopeIndex, sys.argv[2])
            showobj(scope)
        elif command == 'site':
            site = get(net.builder.sites, net.builder.siteIndex, sys.argv[2])
            showobj(site)
        elif command == 'switch':
            switch = get(net.builder.switches, net.builder.switchIndex, sys.argv[2])
            showobj(switch)
        elif command == 'vpn':
            vpn = get(vpns, vpnIndex, sys.argv[2])
            showobj(vpn)

if __name__ == '__main__':
    main()