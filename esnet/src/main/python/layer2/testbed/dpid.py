#!/usr/bin/python
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

from array import array

class Vendors:
    OVS = 1
    Corsa = 2

class Roles:
    POPHwSwitch = 1    # Hardware based SDN connected to production router (managed by ENOS)
    POPSwSwitch = 2    # Software switch connected to the HwSwitch (managed by ENOS)
    UserSwSwitch = 3   # Software switch connnect to the SwSwitch, but managed by end-user controller (i.e. not ENOS)


def encodeDPID (location,vendor,role, id):
    """
    Generates a DPID that is encoded as follow:
    DPID format: byte7 byte6   byte5   byte4 byte3 byte2 byte1 byte0
                 vendor type  reserved  <--- ASCII Name ------>  id

    :param location: 4 letters max. location (i.e. STAR, LBNL).
    :param vendor: Must be part of the Vendors class
    :param role: Must be part of Roles
    :param id:
    :return:
    """

    loc = array('B',location[0:4])
    loc = (4 - len(location[0:4])) * array('B',[0]) + loc # Left padding
    dpid = array('B',[vendor]) + array('B',[role,0]) + loc + array('B', [id])
    return dpid

def decodeDPID (dpid):
    vendor = dpid[0]
    role = dpid[1]
    id = dpid [7]
    location = dpid [3:7].tostring()
    return (vendor,role,location,id)









