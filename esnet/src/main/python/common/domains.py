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
    """
    This base class defines the generic API to a domain. A domain is set of network elements, including hosts,
    that share the same administrative authority. For instance, ESnet is a domain, but a DTN or TBN, even
    part of ESnet are individual domains.
    A domain includes the 'services' property which is a dict of Services indexed by their type.
    Classes that extend Domain must implement the 'getEdges' method that returns a list of edge routers or switches of
    domain.
    """
    def __init__(self,name,props={}):
        Properties.__init__(self,name=name,props=props)
        self.props['services'] = {}

    def getEdges(self):
        """
        Returns a list of Port's of the domain that is connected to other domains. Each port in the list
        has a property 'toDomains' which is a list of domains this port is connected to.
        :return: [Port]
        """
        return None


class Service (Properties):
    """
    Service is the base class for all services. The base class only defines a property 'type' which describes
    what the service is.
    """
    def __init__(self,name,type,props={}):
        Properties.__init__(self,name=name,props=props)
        self.props['type'] = type

