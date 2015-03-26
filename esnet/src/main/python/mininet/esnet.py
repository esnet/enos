from src.main.python.common.intent import ProvisioningRenderer

class ESnetRenderer(ProvisioningRenderer):
    """
    Provision the data path within ESnet. This is done by setting up all the L2 flowmods
    """