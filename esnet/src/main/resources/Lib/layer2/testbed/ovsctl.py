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

from layer2.testbed.topology import TestbedTopology
from layer2.testbed.dpid import encodeDPID, Vendors, Roles, encodeDPID, decodeDPID
from net.es.netshell.api import Switch, Container

import subprocess
import threading

if not 'ovsCtlLock' in globals():
    ovsCtlLock = threading.Lock()
    globals()['ovsCtlLock'] = ovsCtlLock

CONFIGFILE="/etc/network/interfaces"
CONTAINER_NAME="ovsctl"


def addConfig(interfaces,config=None,viewOnly=False):
    if config == None:
        config = CONFIGFILE
    f = None
    inInterface = False
    lines = mergeConfig(interfaces=interfaces,config=config)
    if not viewOnly:
        f = open (config,'w')
    for line in lines:
        if line.startswith("auto") or line.startswith("allow"):
            inInterface = False
        if inInterface:
            line = "\t" + line
        if viewOnly:
            print line
        else:
            f.write(line + "\n")
        if line.startswith('iface'):
            inInterface= True
    if not viewOnly:
        f.flush()
        f.close()


def deleteFromConfig(name,config=None,viewOnly=False):
    if config == None:
        config = CONFIGFILE
    f = None
    inInterface = False
    lines = parseConfig(config=config)
    if not viewOnly:
        f = open (config,'w')
    doSkip = False
    for line in lines:
        if line.startswith("auto") or line.startswith("allow"):
            inInterface = False
            doSkip = False
        if inInterface:
            line = "\t" + line
        if line.startswith("auto"):
            if line.split(" ")[1] == name:
                continue
        if line.startswith('iface'):
            inInterface= True
            if line.split(" ")[1] == name:
                doSkip = True
                continue
        if not doSkip:
            if viewOnly:
                print line
            else:
                f.write(line + "\n")

    if not viewOnly:
        f.flush()
        f.close()

def mergeConfig (interfaces,config=None):
    if config == None:
        config=CONFIGFILE
    f = open(config)
    lines = f.readlines()
    print "config",config,lines
    writeLines = []
    inInterface = False
    inMerge = False
    seen = []
    for line in lines:
        line = line.split("\n")[0].lstrip().rstrip()
        if line == '\n':
            writeLines.append("")
            continue
        if line.startswith('iface'):
            name = line.split(" ")[1]
            seen.append(name)
            if name in interfaces:
                inMerge = True
                interface = interfaces[name]
                for l in interface:
                    writeLines.append(l)
            else:
                writeLines.append(line)
            inInterface = True
            continue
        if line.startswith("auto") or line.startswith("allow"):
            inInterface = False
            inMerge = False

        if inInterface and inMerge:
            continue
        writeLines.append(line)

    for interface in interfaces:
        if not interface in seen:
            writeLines.append("\n")
            for l in interfaces[interface]:
                writeLines.append(l)

    return writeLines

def parseOvsExtra(line):
    entries = []
    patches = line.split("ovs_extra ")[1].split("add-port ")
    for patch in patches:
        if len(patch):
            continue
        entry = patch.split(" -- ")[0].split("-")
        entries.append(entry[0],entry[1],entry[2])
    return entries

def parseConfig(config=None):
    if config == None:
        config=CONFIGFILE
    f = open(config)
    lines = f.readlines()
    interfaces={}

    inInterface = False
    interface = None
    for line in lines:
        line = line.split("\n")[0].lstrip().rstrip()
        if line == '\n':
            continue
        if line.startswith('iface'):
            name = line.split(" ")[1]
            interface = []
            interface.append (line)
            interfaces[name] = interface
            inInterface = True
            continue
        if line.startswith("auto") or line.startswith("allow"):
            inInterface = False

        if inInterface:
            x = line.split(" ")
            interface.append(line)

    f.close()
    return interfaces

def newInterface(name,mtu=9000,ctrl=None,dpid=None):
    interface = []
    interface.append("auto " + name)
    interface.append("iface " + name + " inet manual")
    interface.append("ovs_type OVSBridge")
    interface.append("mtu " + str(mtu))
    if ctrl != None:

    if dpid != None:
        interface.appemd("")
    return interface

class UserSwitch(Switch):
    def __init__(self, name, owner=None,domain=None):
        if domain != None:
            super(UserSwitch, self).__init__(name,domain=domain,props=props)
        else:
            super(UserSwitch, self).__init__(name,props=props)
        self.props['role'] = 'UserSwitch'
        self.props['pop'] = None
        self.props['controller'] = None
        self.props['dpid'] = None
        self.props['owner'] = owner

def newDPID(name=None):
    with ovsCtlLock:
        if name == None:
            name = "user"
        else:
            name = name[:4]
        container = Container.getContainer(getContinerName())
        userSwitchIndex = 1
        if ("userSwitchIndex" in container.properties):
            userSwitchIndex = container.properties["userSwitchIndex"]
        dpid = encodeDPID(vendor=Vendors.OVS,role=Roles.UserSwSwitch,location=name,id=userSwitchIndex)
        container.properties["userSwitchIndex"] = userSwitchIndex + 1
        container.save()
        return dpid

def ovsctl(cmds):
    full = ['of-vsctl'] + cmds
    res = subprocess.call(full)
    if res == 1:
        return False
    else:
        return True

def getContinerName():
    hostname = subprocess.check_output(["uname","-n"])[:-1]
    hostname = "_".join(hostname.split("-"))
    return CONTAINER_NAME + "_" + hostname

def exists(name,config=None):
    interfaces = parseConfig(config)
    return name in interfaces


def localCreate(name, ctrl=None,dpid=None, config=None):
    if exists(name):
        return(None,"Switch's name already exist")
    res = ovsctl(['add-br',name])
    if not res:
        return (None,"Cannot create OVS swtch")
    switch = UserSwitch(name=name)
    if ctrl != None:
        if dpid == None:
            dpid = newDPID(name)
        # set openflow
        res = ovsctl(['set-fail-mode',name,'secure'])
        if not res:
            return (switch,"Cannot set set-fail-mode")
        # set DPID
        res = ovsctl(['set','bridge',name,"other-config:datapath-id="+dpid])
        if not res:
            return (switch,"Cannot set DPID")
        switch.properties['dpid'] = dpid
        # set controller
        if not ':' in ctrl:
            ctrl += ":6633"
        ctrl = "tcp:" + ctrl
        res = ovsctl(['set-controller',name,ctrl])
        if not res:
            return (switch,"Cannot set controller")
        switch.properties['controller'] = ctrl
    interface = newInterface(name=name,ctrl=ctrl,dpid=dpid)
    addConfig(interfaces={name:interface},config=config)
    container = Container.getContainer(getContinerName())
    container.saveResource(switch)
    return (switch,None)


def localDelete(name,config=None):
    if not exists(name):
        return(False,"Switch does not exist")
    res = ovsctl(['del-br',name])
    if not res:
        return (False,"Cannot delete OVS swtch")
    deleteFromConfig(nameconfig=config)
    container = Container.getContainer(getContinerName())
    container.deleteResource(name)
    return(True,None)

def addlink (src,dst):


def print_syntax():
    print
    print "Testbed OVS Utility."
    print "\novsctl <cmd> <cmds options>"
    print "\n\tCommands are:\n"
    print "\n\thelp: prints this help."
    print "\n\tshow-switch <switch-name> | all> [grep <string>] Displays a switch by its name or all switches."
    print "\n\t\tAn optional string to match can be provided."
    print "\n\tcreate <switch-name> [ctrl <host | host:port> [dpid <dpid>]] Creates a switch in a SDN POP"
    print "\n\tdelete <switch-name> delete switch"
    print "\n\tadd-link <src switch name>  <dest switch>"
    print "\n\tdel-link <src switch name>  <dest switch>"

# Retrieve topology
if not 'topo' in globals() or topo == None:
    topo = TestbedTopology()
    globals()['topo'] = topo

if __name__ == '__main__':
    if not 'topo' in globals() or topo == None:
        topo = TestbedTopology()
    globals()['topo'] = topo
    argv = sys.argv
    if len(argv) == 1:
        print_syntax()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_syntax()
    name = argv[2]
    if cmd == "create":
        if 'pop' in argv:
            pop = topo.builder.popIndex[sys.argv[4]]
            print "not implemented yet"
        else:
            (sw,error) = localCreate(name,config="/tmp/i2")
            if error != None:
                print "failed:",error
            else:
                print "switch is created"
    elif cmd == "delete":
        if 'pop' in argv:
            pop = topo.builder.popIndex[sys.argv[4]]
            print "not implemented yet"
        else:
            (ok,msg) = localDelete(name,config="/tmp/t2")
            if not ok:
                print "failed:",msg
            else:
                print "switch is deleted"
    elif cmd == "add-link":
        src = sys.argv[2]
        dst = sys.argv[3]
        (ok,msg) = addlink(src=src,dst=dst)
        if not ok:
            print "failed:",msg
        else:
            print "switches haves been linked"
