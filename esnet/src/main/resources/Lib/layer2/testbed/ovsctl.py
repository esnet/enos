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
from layer2.common.api import Switch

from net.es.netshell.kernel.exec import KernelThread

import subprocess
import threading

if not 'ovsCtlLock' in globals():
    ovsCtlLock = threading.Lock()
    globals()['ovsCtlLock'] = ovsCtlLock

class UserSwitch(Switch):
    logger = Logger('UserSwitch')
    def __init__(self, name, domain=None, props={}):
        if domain != None:
            super(UserSwitch, self).__init__(name,domain=domain,props=props)
        else:
            super(UserSwitch, self).__init__(name,props=props)
        self.props['role'] = 'UserSwitch'
        self.props['pop'] = None
        self.props['controller'] = None
        self.props['dpid'] = None
        self.props['owner'] = KernelThread.currentKernelThread().getUser().getName()


def newDPID(name=None):
    with ovsCtlLock:
        global userSwitchIndex
        if name == None:
            name = "user"
        else:
            name = name[:4]
        dpid = encodeDPID(vendor=Vendors.OVS,role=Roles.UserSwSwitch,location=name,id=userSwitchIndex)
        userSwitchIndex += 1
        return dpid


def ovsctl(cmds):
    full = ['of-vsctl']
    full = full + cmds
    res = subprocess.call(full)
    if res == 1:
        return False
    else:
        return True

def localCreate(name, dpid=None):

    with ovsCtlLock:
        if name in userSwitches:
            return(None,"Switch's name already exist")
        res = ovsctl(['add-br',name])
        if not res:
            return (None,"Cannot create OVS swtch")
        if dpid == None:
            dpid = newDPID(name)
        # set DPID
        res = ovsctl('set','Bridge',name,"other-config:datapath-id="+dpid)
        switch = UserSwitch(name=name)
        userSwitches[name] = switch
        if not res:
            return (switch,"Cannot set DPID")
        switch.props['dpid'] = dpid
        return (switch,None)


def localDelete(name):

    with ovsCtlLock:
        if not name in userSwitches:
            return(None,"Switch does not exist")
        switch = userSwitches[name]
        res = ovsctl(['del-br',name])
        if not res:
            return (switch,"Cannot delete OVS swtch")
        userSwitches.pop(name)
        return (switch,None)

def print_syntax():
    print
    print "ovsctl <cmd> <cmds options>"
    print "Manages custom OVS switches."
    print "\tCommands are:\n"
    print "\thelp: prints this help."
    print "\tshow-switch <switch-name> | all> [grep <string>] Displays a switch by its name or all switches."
    print "\t\tAn optional string to match can be provided."
    print "\tcreate <switch-name> [pop <pop-name>] Creates a switch in a SDN POP"
    print "\tdelete <switch-name> delete switc [pop <pop-name>] h"
    print "\tset-ctrl <switch-name> ctrl <ip> set the controller [pop <pop-name>]"


if not 'userSwitches' in globals() or userSwitches == None:
    userSwitches = {}
globals()['userSwicthes'] = userSwitches

if not 'userSwitchIndex' in globals() or userSwitchIndex == None:
    userSwitchIndex = 1
globals()['userSwitchIndex'] = userSwitchIndex
# Retrieve topology
if not 'topo' in globals() or topo == None:
    topo = TestbedTopology()
    globals()['topo'] = topo

if __name__ == '__main__':
    if not 'topo' in globals() or topo == None:
        topo = TestbedTopology()
    globals()['topo'] = topo
    if not 'userSwitches' in globals() or userSwitches == None:
        userSwitches = {}
    globals()['userSwicthes'] = userSwitches
    if not 'userSwitchIndex' in globals() or userSwitchIndex == None:
        userSwitchIndex = 1
    globals()['userSwitchIndex'] = userSwitchIndex
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
            (sw,error) = localCreate(name)
            if error != None:
                print "failed:",error
            else:
                print "switch is created"
    elif cmd == "delete":
        if 'pop' in argv:
            pop = topo.builder.popIndex[sys.argv[4]]
            print "not implemented yet"
        else:
            (sw,error) = localDelete(name)
            if error != None:
                print "failed:",error
            else:
                print "switch is created"