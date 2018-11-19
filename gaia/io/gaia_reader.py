from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)
from future.utils import with_metaclass

from gaia.gaia_data import GaiaDataObject
from gaia.util import (
    GaiaException,
    MissingParameterError,
    MissingDataException,
    UnsupportedFormatException,
    get_uri_extension
)


class GaiaReaderFactoryMetaclass(type):
    """
    This is the metaclass for any type deriving from GaiaReader, providing
    us with a registry of possible readers, which we can use to look for an
    appropriate subtype at runtime, based on constructor args.
    """
    _registry = {}

    """
    Make sure we include every GaiaReader subtype in our registry.
    """
    def __new__(cls, clsname, bases, dct):
        classtoreturn = super(GaiaReaderFactoryMetaclass,
                              cls).__new__(cls, clsname, bases, dct)
        GaiaReaderFactoryMetaclass._registry[clsname] = classtoreturn
        return classtoreturn

    """
    Intercept the constructor arguments generically generally when attempting
    to instantiate a reader.  If we aren't in here via direct use of the
    GaiaReader class itself, then the developer probably knows what specific
    subtype she wants, so we make sure she gets that.  Otherwise, we will use
    some heuristic to choose the subtype we construct.  If we see a
    'reader_class' keyword argument, we try to choose that class.  If not, we
    iterate through all the registered readers, looking for a subclass with a
    static "can_read" method which returns true given the specific constructor
    arguments we got.  Currently we construct the first one of these we find.
    """
    def __call__(cls, *args, **kwargs):
        registry = GaiaReaderFactoryMetaclass._registry
        subclass = None
        instance = None

        if id(cls) != id(GaiaReader):
            # Allow for direct subclass instantiation
            instance = cls.__new__(cls, args, kwargs)
        else:
            if 'reader_class' in kwargs:
                classname = kwargs['reader_class']
                if classname in registry:
                    subclass = registry[classname]
            else:
                for classname, classinstance in registry.items():
                    if hasattr(classinstance, 'can_read'):
                        canReadMethod = getattr(classinstance, 'can_read')
                        if canReadMethod(*args, **kwargs):
                            subclass = classinstance
                            # FIXME:
                            break

            if subclass:
                instance = subclass.__new__(subclass, args, kwargs)
            else:
                argsstr = 'args: %s, kwargs: %s' % (args, kwargs)
                msg = 'Unable to find GaiaReader subclass for: %s' % argsstr
                raise GaiaException(msg)

        if instance is not None:
            instance.__init__(*args, **kwargs)

        return instance


class GaiaReader(with_metaclass(GaiaReaderFactoryMetaclass, object)):
    """
    Abstract base class, root of the reader class hierarchy.
    """
    def __init__(self, *args, **kwargs):
        pass

    """
    Return a GaiaDataObject
    """
    def read(self, data_source, format=None, epsg=None):
        return GaiaDataObject(reader=self)

    def load_metadata(self, dataObject):
        print('GaiaReader _load_metadata()')

    def load_data(self, dataObject):
        print('GaiaReader _load_data()')
