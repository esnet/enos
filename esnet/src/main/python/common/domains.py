from common.api import Properties

class Directory (Properties):
    def __init__(self,name="",props={}):
        Properties.__init__(self,name=name,props=props)
        self.props['domains'] = {}

    def getService(self,domain,type):
        return None

    def registerService (self,domain):
        if not domain in self.props['domains']:
            self.props['domains'][domain.name] = domain
            return True
        else:
            return False

class Domain (Properties):
    def __init__(self,name,props={}):
        Properties.__init__(self,name=name,props=props)
        self.props['services'] = {}

    def getEdges(self):
        return None


class Service (Properties):
    def __init__(self,name,type,props={}):
        Properties.__init__(self,name=name,props=props)
        self.props['type'] = type

