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
from net.es.netshell.api import GenericGraphViewer

from common.intent import Expectation
from common.intent import Intent

def usage():
    print "usage:"
    print "graph expecatation $INDEX: graph a single expectation (by name)"
    print "graph intent $INDEX: graph a single intent (by name)"

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
    elif len(command_args) < 4:
        usage()
    elif command_args[2] == 'expectation':
        expectation = get(None, Expectation.directory, command_args[3])
        g = expectation.props['topology']
        gv = GenericGraphViewer(g)
        gv.display()
    elif command_args[2] == 'intent':
        intent = get(None, Intent.directory, command_args[3])
        g = intent.graph
        gv = GenericGraphViewer(g)
        gv.display()

if __name__ == '__main__':
    main()