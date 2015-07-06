import uuid
import logging
import sys
import array
import struct, array
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

def print_stack():
    tid = threading.current_thread().ident
    frame = inspect.currentframe()
    while frame:
        print '[%r] %r:%r' % (tid, frame.f_code, frame.f_lineno)
        frame = frame.f_back
