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

from net.es.netshell.api import GenericSite

import threading

sites = {}

if not 'sitesLock' in globals():
    sitesLock = threading.Lock()
    globals()['sitesLock'] = sitesLock


def getSite(name):
    global sites
    if not name in sites:
        return None
    return sites[name]

def createSite(name):
    global sites
    with sitesLock:
        if name in sites:
            return None
        site = GenericSite(name)
        sites[name] = site
        return site

def print_syntax():
    print
    print "sitectl <cmd> <cmds options>"
    print "Manages testbed sites."
    print "\tCommands are:\n"
    print "\thelp: prints this help."
    print "\tshow-site <site-name | all> [grep <string>] Displays a site by its name or all sites"
    print "\t\tAn optional string to match can be provided."
    print "\tcreate <site-name> pop|switch <pop-name|switch-name>. A site is either directly connected"
    print "\t\tto a SDN POP or to a custom existing software switch."
    print "\tdelete <site-name> delete site"
    print "\tadd-link <site-name> gri <gri|auto|new> Adds an existing OSCARS circuit connecting the site"
    print "\t\tto its SDN POP. When 'auto' is provided, the commands tries to discover the OSCARS circuit."
    print "\t\tThe command will create a new link when 'new' is provided."
    print "\trem-link <site-name> gri <gri> Removes a link from the site"
    print "\tadd-host <site-name> host <host-name> [ip <ip-address/netmask>] [vlan <vlan-id>]"
    print "\t\tadd an existing host into the site. Optionally an IP address and a VLAN can be provided."
    print "\trem-host <site-name> host <host-name>: removes a host from a site."



if __name__ == '__main__':
    argv = sys.argv
    if len(argv) == 1:
        print_syntax()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_syntax()
    elif cmd == "create":
        sitename = argv[2]
        site = createSite(name)
        if site == None:
            print "error: there is already a site with the same name"
            sys.exit()



