import logging
import sys
import array
import struct, array, jarray


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

def dump(obj):
	print "dump " + str(obj.__class__) + ":", obj
	for attr in dir(obj):
		if attr[0:2] == '__':
			continue
		if attr == "props":
			print "\t" + attr + ":"
			for prop in obj.props.items():
				if not isinstance(prop[1], dict) and not isinstance(prop[1], list):
					print "\t\t" + prop[0] + str(prop[1].__class__), prop[1]
				else:
					print "\t\t" + prop[0] + str(prop[1].__class__)
		else:
			var = getattr(obj, attr)
			if not isinstance(var, dict) and not isinstance(var, list):
				print "\t" + attr + str(var.__class__), var
			else:
				print "\t" + attr + str(var.__class__)
