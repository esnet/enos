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

import subprocess

def print_syntax():
    print
    print "ovsctl <cmd> <cmds options>"
    print "Manages custom OVS switches."
    print "\tCommands are:\n"
    print "\thelp: prints this help."
    print "\tshow-switch <switch-name> | all> [grep <string>] Displays a switch by its name or all switches"
    print "\t\tAn optional string to match can be provided."
    print "\tcreate <switch-name> [pop <pop-nqme>] Creates a switch on a SDN POP"
    print "\tdelete <switch-name> delete switch"
    print "\tset-ctrl <switch-name> ctrl <ip> set the controller"


def ovsctl(cmds):
    full = ['of-vsctl']
    full = full + cmds
    res = subprocess.call(full)
    if res == 1:
        return False
    else:
        return True

def localCreate(name, dpid=None):
    res = ovsctl(['add-br',name])
    if not res:
        return None






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
    if cmd == "create":
        name = argv[2]
        if 'pop' in argv:
            pop = topo.builder.popIndex[sys.argv[4]]
            print "not implemented yet"
        else:
            localCreate(name)