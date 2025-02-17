"""
Author: Dr. Azad Rasul
Affiliation: Soran University
Email: azad.rasul@soran.edu.iq
Year: 2025
"""
from .lst_plugin import LSTCalculator
def classFactory(iface):
    return LSTCalculator(iface)
