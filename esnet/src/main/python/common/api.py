
class Properties(object):
    def __init__(self, name,props={}):
        self.name = name
        self.props = props.copy()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class Port(Properties):
    def __init__(self,name,props={}):
        Properties.__init__(self,name,props)
    def __str__(self):
        desc = "port: "
        if 'switch'in self.props:
            desc += self.props['switch'].name + "/" + self.name
        else:
            desc += "unknown switch:" + self.name
        if 'vlan' in self.props:
            desc += " vlan= " + str(self.props['vlan'])
        desc += "\n"
        return desc

    def __repr__(self):
        return self.__str__()

class Node(Properties):
    def __init__(self, name,builder=None,props={}):
        """

        :type builder: TopoBuilder
        """
        Properties.__init__(self,name,props)
        self.props['ports'] = {}
        self.interfaceIndex = 1
        if builder:
            builder.nodes[name] = self

    def newPort(self,props={}):
        port = Port(name= "eth" + str(self.interfaceIndex),props=props)
        self.props['ports'][port.name] = port
        port.props['node'] = self.name
        self.interfaceIndex += 1
        return port

class SDNPop(Properties):
    def __init__(self,name,props={}):
        Properties.__init__(self,name,props)

class VPN(Properties):
    def __init__(self,name,props={}):
        Properties.__init__(self,name,props)
        self.props['sites'] = {}

class Site(Properties):
    def __init__(self,name,props={}):
        Properties.__init__(self,name,props)
        self.props['hosts'] = {}
        self.props['links'] = {}

class Link(Properties):
    def __init__(self,name,props={}):
        Properties.__init__(self,name,props)
        self.props['endpoints'] = []

