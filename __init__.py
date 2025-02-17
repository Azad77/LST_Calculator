from .lst_plugin import LSTCalculator
def classFactory(iface):
    return LSTCalculator(iface)