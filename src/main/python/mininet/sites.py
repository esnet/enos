from intent import ProvisioningRenderer

class SiteRenderer(ProvisioningRenderer):
    """
    Implements the rendering of provisioning intents on the Site. This class is responsible for pushing the proper
    flowMods that will forward packets between the hosts and the ESnet border router. Typically the topology is

         host(s) <-> siteRouter <-> borderRouter

         Simple vlan/port mach and outport /vlan on siteRouter needs to be set
    """
    def __init__(self,hosts, siteRouter,borderRouter):
        """
        Creates a SiteRenderer which provision the path betweeen the endpoint hosts and the ESnet
        border router. The topology is assumed to be a set of hosts, connected to an openflow switch
        "siteRouter" which is itself connected to an openflow switch "ESnet borderRouter"
        :param hosts: ([TestbedHost])array of hosts
        :param siteRouter: (OpenFlowSwitch) site OpenFlow switch
        :param borderRouter: (OpenFlowSwitch) ESnet OpenFlow border router
        :return:
        """

    def __init__(self, intent):
        """
        Generic constructor. Translate the intent
        :param intent:
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
