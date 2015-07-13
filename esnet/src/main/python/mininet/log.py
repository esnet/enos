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

def usage(supportedNames):
    print "usage:"
    for name in supportedNames:
        print "log %s: show the level of controller log" % name
        print "log %s $LEVEL: set the level of controller log" % name
    print "LEVEL: 10: debug; 20: info; 30: warning; 40: error"

def log(args):
    """
    args[0]: name
    args[1]: level (optional)
    """
    name = args[0]
    level = Logger(name).level
    desc = "log level of %s = %d" % (name, level)
    if len(args) >= 2:
        try:
            new_level = int(args[1])
            Logger(name).setLevel(new_level)
            desc += "->%d" % new_level
        except:
            pass
    print desc

def main():
    """
    command_args[0]: python
    command_args[1]: .../log.py
    command_args[2:]: customized arguments
    """
    if not 'net' in globals():
        print "Please run demo first"
        return
    supportedNames = ['ODLClient', 'SimpleController', 'SiteRenderer', 'SDNPopsRenderer', 'L2SwitchScope']
    if len(command_args) < 3:
        usage()
    elif command_args[2] in supportedNames:
        log(command_args[2:])
    else:
        print "unknown command..."
        usage(supportedNames)

if __name__ == '__main__':
    main()