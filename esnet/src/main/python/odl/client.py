
class ODLClient(object):
    _instance = None


    def __new__(cls, *args, **kwargs):
        """
        Implements a singleton
        """
        if not cls._instance:
            cls._instance = super(ODLClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance