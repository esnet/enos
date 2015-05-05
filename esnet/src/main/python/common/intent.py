from common.utils import generateId
from common.api import Properties

class Intent(Properties):
    """
    An intent is the description of what is needed to be done, the intention of the caller, rather than the
    prescription, or telling what to do. Intents are rendered by renderer that know how to implement the intent,
    knowing how and what to do.
    The Intent class defines two variable members, self.id, a string containing a UUID and self.description that
    is a dictionary of "description". A description is a key/value pair where the key is the generic name (or type)
    of the description, and the value is an object holding the description.
    """
    def __init__(self,name,props={}):
        Properties.__init__(self,name=name,props=props)
        self.id = generateId()
        self.name = name
        self.props = props
        Intent.directory[name] = self

    directory = {}


class Expectation(Properties):
    """
    An expectation is the expression of the current state of the rendering of an intent.
    TBD.
    """
    def __init__(self,name,renderer,intent,props={}):
        Properties.__init__(self,name=name,props=props)
        self.id = generateId()
        self.name = name
        self.props = props
        self.intent = intent
        self.renderer = renderer
        Expectation.directory[name] = self

    directory = {}


class Renderer:
    """
    A renderer implements or "renders" intents. To do so, it may or not create intents to other renderer or render
    directly all or parts of the intent.
    """
    def __init__(self, intent):
        """
        Creates a new rendering of the provided intent.
        :param intent (Intent):
        :return:
        """
        #Properties.__init__(self,name=intent.name,props=props)
        Renderer.directory[intent.name] = self

    def execute(self):
        """
        Renders the intent.
        :return: Expectation when succcessful, None otherwise
        """
        return None

    def destroy(self):
        """
        Destroys or stop the rendering of the intent.
        """

    directory = {}


class ProvisioningIntent(Intent):
    """
    A generic intent that expresses a provisioning intention. It includes the following descriptions:
        "topology": (net.es.netshell.api.GenericGraph) describing the logical topology of the intended
                    provisioning.
    """
    def __init__(self,name,graph,props={}):
        """
        Creates a provisioning intent providing a GenericGraph of the logical view of the
        topology that is intended to be created.
        """
        Intent.__init__(self,name,props)
        self.props['topology'] = graph

    def buildGraph(self):
        """
        Builds and return the topology graph of the intent.
        """
        return None



class ProvisioningRenderer(Renderer):
    """
    A Generic Renderer that knows how to render provisioning intents
    """
    def __init__(self,name,props={}):
        Renderer.__init__(self,name,props)


class ProvisioningExpectation(Expectation):
    def __init__(self,name,renderer,intent,graph,props={}):
        Expectation.__init__(self,name=name,renderer=renderer,intent=intent,props=props)
        self.props['topology'] = graph



