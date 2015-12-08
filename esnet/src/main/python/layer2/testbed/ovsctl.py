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


def print_syntax():
    print
    print "ovsctl <cmd> <cmds options>"
    print "Manages custom OVS switches."
    print "\tCommands are:\n"
    print "\thelp: prints this help."
    print "\tshow-switch <switch-name> | all> [grep <string>] Displays a switch by its name or all switches"
    print "\t\tAn optional string to match can be provided."
    print "\tcreate <switch-name> pop <pop-nqme> Creates a switch on a SDN POP"
    print "\tdelete <switch-name> delete switch"
    print "\tset-ctrl <switch-name> ctrl <ip> set the controller"



if __name__ == '__main__':
    argv = sys.argv
    if len(argv) == 1:
        print_syntax()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_syntax()
