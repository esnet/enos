import uuid

"""
This method is used to implement a singleton. In order to make a singleton class:

from common.api import singleton

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