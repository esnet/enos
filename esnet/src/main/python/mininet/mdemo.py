from mininet.mac import MACAddress
from mininet.mat import MATManager
from mininet.mcallback import MiniTest
from mininet.utility import InitLogger
import random
random.seed(0)
MATManager.reset()
InitLogger()
# Logger().setLevel(logging.DEBUG)
if 'c' in vars() or 'c' in globals():
    del c
c = MiniTest()
