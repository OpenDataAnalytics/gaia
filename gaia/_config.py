"""This module contains the global configuration for gaia.

Submodules and plugins can store any user/site configuration data
in this object (in a unique section).
"""

from six.moves import configparser
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

ConfigParser = configparser.ConfigParser
if hasattr(configparser, 'SafeConfigParser'):  # pragma: nocover
    ConfigParser = configparser.SafeConfigParser

kw = {
    'dict_type': OrderedDict
}
if hasattr(configparser, 'ExtendedInterpolation'):  # pragma: nocover
    kw['interpolation'] = configparser.ExtendedInterpolation()

config = ConfigParser(**kw)

__all__ = ('config',)
