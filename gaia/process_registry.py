from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

from gaia import GaiaException


"""
A process is just two stateless methods, 'validate' and 'compute',
associated with a process name.
"""

"""
By making this is a module-level variable, anyone who imports the module
has access to the single, global registry.  This avoids the need for some
bootstrapping code that instantiates a single registry and makes it
available to the whole application.
"""
__process_registry = {}


def find_processes(processName):
    """
    Return a list of registry entries that implement the named process.
    """
    if processName in __process_registry:
        return __process_registry[processName]
    return None


def register_process(processName):
    """
    Return a process registration decorator
    """
    def processRegistrationDecorator(computeMethod):
        if processName not in __process_registry:
            __process_registry[processName] = []
        __process_registry[processName].append(computeMethod)
        return computeMethod
    return processRegistrationDecorator


def list_processes(processName=None):
    """
    Display a list of the processes in the registry, for debugging or
    informational purposes.
    """
    def display_processes(name, plist):
        print('%s processes:' % name)
        for item in plist:
            print(item)

    if processName is not None:
        if processName in __process_registry:
            display_processes(processName, __process_registry[processName])
        else:
            print('No processes registered for %s' % processName)
    else:
        for pName in __process_registry:
            display_processes(pName, __process_registry[pName])


def compute(processName, inputs, args):
    """
    Just looks up a process that can do the job and asks it to 'compute'
    """
    processes = find_processes(processName)

    if not processes:
        list_processes(processName)
        raise GaiaException('Unable to find suitable %s process' % processName)

    for p in processes:
        # How will we choose between equally "valid" processes?  For now
        # just return the first one.
        try:
            return p(inputs, args)
        except GaiaException:
            pass

    raise GaiaException('No registered processes were able to validate inputs')
