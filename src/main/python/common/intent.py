from net.es.netshell.api import PersistentObject
class Intent (PersistentObject):
    def __init__(self):
        print "init"

    def setIntentId(self, intentId):
        self.intentId = intentId
    def getIntentId(self):
        return self.intentId





