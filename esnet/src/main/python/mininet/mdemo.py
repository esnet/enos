import mininet.utility
import mininet.mac
import mininet.mat
import mininet.mcallback
reload(mininet.mac)
reload(mininet.mat)
reload(mininet.utility)
reload(mininet.mcallback)
from mininet.mac import MACAddress
from mininet.mcallback import MiniTest
from mininet.utility import InitLogger, javaByteArray, broadcastAddress
import random
random.seed(0)
MATManager.reset()
InitLogger()
# Logger().setLevel(logging.DEBUG)
if 'c' in vars() or 'c' in globals():
    del c
c = MiniTest()
