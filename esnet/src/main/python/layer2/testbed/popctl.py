#!/usr/bin/python
#
# ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
# of the University of California, through Lawrence Berkeley National
# Laboratory (subject to receipt of any required approvals from the
# U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this
# software, please contact Berkeley Lab's Innovation & Partnerships
# Office at IPO@lbl.gov.
#
# NOTICE.  This Software was developed under funding from the
# U.S. Department of Energy and the U.S. Government consequently retains
# certain rights. As such, the U.S. Government has been granted for
# itself and others acting on its behalf a paid-up, nonexclusive,
# irrevocable, worldwide license in the Software to reproduce,
# distribute copies to the public, prepare derivative works, and perform
# publicly and display publicly, and to permit other to do so.
#


from net.es.netshell.api import Container,GenericNode

def createtopo(topology):
    container = Container.createContainer(topology)

def deletetopo(topology):
    container = Container.getContainer(topology)
    if container != None:
        container.deleteContainer()

def addpop(topology,pop):
    container = Container.getContainer(topology)
    if container == None:
        print topology,"does not exist."
        return
    node = GenericNode(pop)
    container.saveResource(node)

def delpop(topology,pop):
    container = Container.getContainer(topology)
    if container == None:
        print topology,"does not exist."
        return
    node = container.loadResource(pop)
    if node == None:
        print node,"does not exist"
        return
    node.delete(container)

def print_syntax():
    print
    print "popctl <cmd> <cmds options>"
    print "popctl <toplogy> <cmd> <cmds options>"
    print "Manages SDN POP topology"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tcreate <topology name>"
    print "\t\tcreates a new topology."
    print "\tdelete <topology name>"
    print "\t\tdeletes a new topology."
    print "\t<topology> add-pop <pop name>:"
    print "\t\t adds an SDN POP in the topology."
    print "\t<toploogy> del-pop <pop name>:"
    print "\t\t deletes an SDN POP in the topology."
    print "\t<toploogy> add-link <src> <dst> [both]:"
    print"\t\tCreates a link between two nodes of the topology. If the option both is provided,"
    print"\t\tthe opposite links is automatically added."
    print "\t<toploogy> del-link <src> <dst> [both]:"
    print"\t\tDeletes a link between two nodes of the topology. If the option both is provided,"
    print"\t\tthe opposite links is automatically deleted."

if __name__ == '__main__':
    argv = sys.argv

    if len(argv) == 1:
        print_syntax()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_syntax()
    elif cmd == "create":
        topology = argv[2]
        createtopo (topology)
    elif cmd == "delete":
        topology = argv[2]
        deletetopo (topology)
    else:
        topology = argv[1]
        cmd = argv[2]
        if cmd  == "add-pop":
            pop = argv[3]
            addpop(topology,pop)
        elif cmd == "del-pop":
            pop = argv[3]
            delpop(topology,pop)




