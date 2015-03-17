from utils import generateId

class Intent:
    """
    An intent is the description of what is needed to be done, the intention of the caller, rather than the
    prescription, or telling what to do. Intents are rendered by renderer that know how to implement the intent,
    knowing how and what to do.
    """
    def __init__(self):
        self.id = generateId()


class Expectation:
    """
    An expectation is the expression of the current state of the rendering of an intent.
    TBD.
    """


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

    def render(self):
        """
        Renders the intent.
        :return: Expectation when succcessful, None otherwise
        """
        return None

    def destroy(self):
        """
        Destroys or stop the rendering of the intent.
        """



class ProvisioningIntent(Intent):
    """
    A generic intent that expresses a provisioning intention
    """
    def __init__(self,graph):
        """
        Creates a provisioning intent providing a GenericGraph of the logical view of the
        topology that is intended to be created.
        """
        Intent.__init__()
        self.graph = graph


class ProvisioningRenderer(Renderer):
    """
    A Generic Renderer that knows how to render provisioning intents
    """
    def __init__(self):
        Renderer.__init__()


