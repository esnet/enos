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
def usage(supportedNames):
    print "usage:"
    for name in supportedNames:
        print "log %s: show the level of %s.logger" % (name, name)
        print "log %s $LEVEL: set the level of %s.log" % (name, name)
    print "LEVEL: 10: debug; 20: info; 30: warning; 40: error"

def log(args):
    """
    args[0]: name
    args[1]: level (optional)
    """
    name = args[0]
    if name == 'root':
        logger = Logger()
    else:
        logger = Logger(name)
    level = logger.level
    desc = "log level of %s = %d" % (name, level)
    if len(args) >= 2:
        try:
            new_level = int(args[1])
            logger.setLevel(new_level)
            desc += "->%d" % new_level
        except:
            pass
    print desc

def main():
    """
    sys.argv[0]: .../log.py
    sys.argv[1:]: customized arguments
    """
    if not 'net' in globals():
        print "Please run demo first"
        return
    supportedNames = ['root', 'ODLClient', 'SimpleController', 'SiteRenderer', 'SDNPopsRenderer', 'L2SwitchScope']
    if len(sys.argv) < 2:
        usage(supportedNames)
    elif sys.argv[1] in supportedNames:
        log(sys.argv[1:])
    else:
        print "unknown command..."
        usage(supportedNames)

if __name__ == '__main__':
    main()
