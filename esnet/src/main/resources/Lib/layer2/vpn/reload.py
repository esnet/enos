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
def cleandemomodules():
    mods = []
    toclean=["layer2","testbed","vpn","api","odl"]
    for mod in sys.modules:
        for p in toclean:
            if p in mod:
                mods.append(mod)
    for mod in mods:
        if mod in sys.modules:
            print "Removing " + mod
            sys.modules.pop(mod)
    sys.path_importer_cache={}

if __name__ == '__main__':
    cleandemomodules()
    vpns=[]
    vpnIndex={}
    if 'vpnService' in globals():
        globals().pop('vpnService')
    if 'VPNindex' in globals():
        globals().pop('VPNindex')
    if 'vpnIndexById' in globals():
        globals().pop('vpnIndexById')