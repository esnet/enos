import logging
import sys
import array
import struct, array, jarray
from java.util import HashMap
import inspect

def InitLogger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if len(logger.handlers) == 0:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
def Logger():
    return logging.getLogger()

def dump(obj, props=True, variable=True, method=False, hidden=False):
	print "dump " + str(obj.__class__) + ":", obj
	for attr in dir(obj):
		if attr[0:2] == '__':
			if not hidden:
				continue
		if attr == "props":
			if not props:
				continue
			print "\t" + attr + ":"
			for prop in obj.props.items():
				if not isinstance(prop[1], dict) and not isinstance(prop[1], list):
					print "\t\t" + prop[0] + str(prop[1].__class__), prop[1]
				else:
					print "\t\t" + prop[0] + str(prop[1].__class__)
		else:
			var = getattr(obj, attr)
			if inspect.ismethod(var):
				if not method:
					continue
			else:
				if not variable:
					continue
			if isinstance(var, dict) or isinstance(var, HashMap):
				if len(var) > 0:
					description = "{{{}{}:{}{}}} with len={}".format(var.items()[0][0], var.items()[0][0].__class__, var.items()[0][1], var.items()[0][1].__class__, len(var))
					print "\t" + attr + str(var.__class__) + description
				else:
					print "\t" + attr + str(var.__class__) + " empty"
			elif isinstance(var, list):
				if len(var) > 0:
					description = "[{}{}] with len={}".format(var[0], var[0].__class__, len(var))
					print "\t" + attr + str(var.__class__) + description
				else:
					print "\t" + attr + str(var.__class__) + " empty"
			else:
				print "\t" + attr + str(var.__class__), var
