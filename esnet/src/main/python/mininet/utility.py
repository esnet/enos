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
