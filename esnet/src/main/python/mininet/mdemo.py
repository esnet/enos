reload(mininet.mcallback)
from mininet.mcallback import MiniCallback
if 'c' in vars() or 'c' in globals():
	del c
c = MiniCallback()
