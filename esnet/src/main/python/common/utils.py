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

def InitLogger(level=logging.WARNING):
    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logger.handlers:
        logger.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(thread)d]%(asctime)s-%(name)s-%(levelname)s-%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def Logger(name=None):
    return logging.getLogger(name)

def print_stack():
    tid = threading.current_thread().ident
    frame = inspect.currentframe()
    while frame:
        print '[%r] %r:%r' % (tid, frame.f_code, frame.f_lineno)
        frame = frame.f_back
