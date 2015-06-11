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

def strByteArray(parr):
    """
    Return a colon-separated string representation of a byte array
    :param parr: array of unsigned bytes in python
    :return: string representation
    """
    return str.join(":", ("%02x" % i for i in parr))

def javaByteArray(v):
    """
    Transfer input argument to java byte array
    :param v: input argument; could be python array, list, or string 
    :return: java byte array (mainly used for org.opendaylight.controller.sal.match/action)
    """
    if isinstance(v, array.array) or isinstance(v, list):
        jarr = jarray.zeros(len(v), 'b')
        for i in range(len(jarr)):
            jarr[i] = struct.unpack('b', struct.pack('B', v[i]))[0]
        return jarr
    elif isinstance(v, str):
        jarr = jarray.zeros((len(v)+1)/3, 'b')
        for i in range(len(jarr)):
            jarr[i] = int(v[(3*i):(3*i+3)], 16)
        return jarr
    Logger().Warning("javaByteArray failed due to unknown type...")
    return None

def broadcastAddress():
    return array.array('b',[-1]*6)