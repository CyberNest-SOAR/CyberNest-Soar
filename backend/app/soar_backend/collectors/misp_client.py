from pymisp import ExpandedPyMISP
from core.config import settings

def lookup_misp(indicator):
    # indicator can be IP, domain, or hash
    misp = ExpandedPyMISP(settings.MISP_URL, settings.MISP_KEY, ssl=False)
    return misp.search(controller='attributes', value=indicator)