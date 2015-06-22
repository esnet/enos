if 'demo' in globals() and demo:
	demo.pause()

import mininet.utility
reload(mininet.utility)

from mininet.utility import InitLogger

import ptest.pobject
reload(ptest.pobject)

from ptest.pobject import PMAC
from ptest.pobject import PSwitch, PSiteRouter, PCoreRouter, PHwSwitch
from ptest.pobject import PHost
from ptest.pobject import PController
from ptest.pobject import PPacket
from ptest.pobject import PMatch
from ptest.pobject import PAction
from ptest.pobject import PVPN
from ptest.pobject import test

import ptest.testtopo
reload(ptest.testtopo)

from ptest.testtopo import TestTopo
from ptest.testtopo import TestTopo1
from ptest.testtopo import TestTopo2
from ptest.testtopo import TestTopo3
from ptest.testtopo import TestTopo4
from ptest.testtopo import TestTopo5

import ptest.testdemo
reload(ptest.testdemo)
from ptest.testdemo import TestDemo
from ptest.testdemo import demo
