import uuid
import logging
import sys
import array
import struct, array
if sys.version.find("Java") == -1:
    from types import DictType as HashMap
else:
    from java.util import HashMap
import threading
import inspect

"""
This method is used to implement a singleton. In order to make a singleton class:

from common.utils import singleton

@singleton
class singletonClass:

    ...

"""
def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

def generateId():
    """
    Generate a UUID
    :return:
    """
    return uuid.uuid4()

def InitLogger(level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logger.handlers:
        logger.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(thread)d]%(asctime)s-%(name)s-%(levelname)s-%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
        
def Logger():
    return logging.getLogger()

def subdump(name, obj, tab, verbose=False):
    if not verbose and (isinstance(obj, dict) or isinstance(obj, HashMap)):
        description = "{} with len=0"
        if len(obj) > 0:
            description = "{{{}{}:{}{},...}} with len={}".format(obj.items()[0][0], obj.items()[0][0].__class__, obj.items()[0][1], obj.items()[0][1].__class__, len(obj))
    elif not verbose and isinstance(obj, list):
        description = "[] with len=0"
        if len(obj) > 0:
            description = "[{}{},...] with len={}".format(obj[0], obj[0].__class__, len(obj))
    else:
        description = "{}".format(obj)
    print '\t'*tab + name + str(obj.__class__) + description

def dump(obj, props=True, variable=True, method=False, hidden=False, verbose=False):
    """
    Dump the information of the object
    :param obj: the target object
    :param props: list the properties(props) of the object
    :param variable: dump an attr if it is not a method
    :param method: dump an attr if it is a method
    :param hidden: dump an attr if it is built-in (started with 2 underlines eg. __xxx__)
    :param verbose: dump elements in the list, dict, or HashMap
    """
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
                subdump(prop[0], prop[1], 2)
        else:
            var = getattr(obj, attr)
            if inspect.ismethod(var):
                if not method:
                    continue
            else:
                if not variable:
                    continue
            subdump(attr, var, 1)

def print_stack():
    tid = threading.current_thread().ident
    frame = inspect.currentframe()
    while frame:
        print '[%r] %r:%r' % (tid, frame.f_code, frame.f_lineno)
        frame = frame.f_back
