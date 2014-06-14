"""MyProxy client utils package - contains openssl module for parsing OpenSSL
config files.

NERC DataGrid Project
"""
__author__ = "P J Kershaw"
__date__ = "15/12/08"
__copyright__ = "(C) 2009 Science and Technology Facilities Council"
__license__ = """BSD - See LICENSE file in top-level directory"""
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__revision__ = '$Id: __init__.py 7554 2010-09-29 14:05:23Z pjkersha $'
from ConfigParser import SafeConfigParser


class CaseSensitiveConfigParser(SafeConfigParser):
    '''Subclass the SafeConfigParser - to preserve the original string case of
    config section names
    '''
    def optionxform(self, optionstr):
        '''Extend SafeConfigParser.optionxform to preserve case of option names
        '''
        return optionstr
