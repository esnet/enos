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
def reloadall():
    """
    Reloads the modules that demo depends upon.
    :return:
    """
    from net.es.netshell.odlmdsal.impl import OdlMdsalImpl
    OdlMdsalImpl.getInstance().setPacketInCallback(None)
    import layer2.common.intent
    reload (layer2.common.intent)
    from layer2.common.intent import Intent
    from layer2.common.intent import Expectation
    import layer2.common.utils
    reload (layer2.common.utils)
    from layer2.common.utils import InitLogger
    from layer2.common.utils import Logger
    import layer2.common.api
    reload (layer2.common.api)
    from layer2.common.api import Link
    from layer2.common.api import Port
    from layer2.common.api import Node
    from layer2.common.api import Host
    from layer2.common.api import ServiceVm
    from layer2.common.api import CoreRouter
    from layer2.common.api import HwSwitch
    from layer2.common.api import SwSwitch
    from layer2.common.api import Site
    from layer2.common.api import SDNPop
    from layer2.common.api import VPN
    from layer2.common.api import Wan
    import layer2.common.mac
    reload (layer2.common.mac)
    from layer2.common.mac import MACAddress
    import layer2.vpn.mat
    reload (layer2.vpn.mat)
    from layer2.vpn.mat import MAT
    import layer2.common.intent
    reload (layer2.common.intent)
    import layer2.common.openflow
    reload (layer2.common.openflow)
    from layer2.common.openflow import L2SwitchScope
    from layer2.common.openflow import PacketInEvent
    from layer2.common.openflow import SimpleController
    from layer2.common.openflow import FlowEntry
    from layer2.testbed import oscars
    reload(oscars)
    from layer2.testbed import builder
    reload(builder)
    import layer2.testbed.topology
    reload (layer2.testbed.topology)
    import layer2.odl.client
    reload (layer2.odl.client)
    from layer2.odl.client import ODLClient
    from layer2.vpn.l2vpn import SDNPopsIntent
    from layer2.vpn.l2vpn import SDNPopsRenderer
    from layer2.vpn.l2vpn import FlowStatus
    import layer2.vpn.l2vpn
    reload(layer2.vpn.l2vpn)
    import layer2.vpn.vpn
    reload(layer2.vpn.vpn)

if __name__ == '__main__':
    reloadall()
    import layer2.vpn.demo
    reload(layer2.vpn.demo)
