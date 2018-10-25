from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

from gaia import GaiaException
from gaia import formats
import gaia.types as types


def test_arg_type(args, arg, arg_type):
    """
    Try to cast a process argument to its required type. Raise an
    exception if not successful.
    :param arg: The argument property
    :param arg_type: The required argument type (int, str, etc)
    """
    try:
        arg_type(args[arg])
    except Exception:
        raise GaiaException('Required argument {} must be of type {}'
                            .format(arg, arg_type))


def validate_base(inputs, args, required_inputs=[], required_args=[],
                  optional_args=[]):
    """
    Ensure that all required inputs and arguments are present.
    """
    input_types = []
    errors = []

    for procInput in inputs:
        inputDataType = procInput._getdatatype()
        if inputDataType == types.PROCESS:
            for t in [i for i in dir(types) if not i.startswith("__")]:
                if any((True for x in procInput.default_output if x in getattr(
                        formats, t, []))):
                    inputDataType = getattr(types, t)
                    break
        input_types.append(inputDataType)

    for i, req_input in enumerate(required_inputs):
        if i >= len(input_types):
            errors.append("Not enough inputs for process")
        elif req_input['type'] != input_types[i]:
            errors.append("Input #{} is of incorrect type.".format(i+1))

    if len(input_types) > len(required_inputs):
        if (required_inputs[-1]['max'] is not None and
            len(input_types) > len(required_inputs) +
                required_inputs[-1]['max']-1):
            errors.append("Incorrect # of inputs; expected {}".format(
                len(required_inputs)))
        else:
            for i in range(len(required_inputs)-1, len(input_types)):
                if input_types[i] != required_inputs[-1]['type']:
                    errors.append(
                        "Input #{} is of incorrect type.".format(i + 1))
    if errors:
        raise GaiaException('\n'.join(errors))
    for item in required_args:
        arg, arg_type = item['name'], item['type']
        if arg not in args or args[arg] is None:
            raise GaiaException('Missing required argument {}'.format(arg))
        test_arg_type(args, arg, arg_type)
        if 'options' in item and args[arg] not in item['options']:
            raise GaiaException('Invalid value for {}'.format(item['name']))
    for item in optional_args:
        arg, arg_type = item['name'], item['type']
        if arg in optional_args and optional_args[arg] is not None:
            test_arg_type(optional_args, arg, arg_type)
            argval = args[arg]
            if 'options' in item and argval not in item['options']:
                raise GaiaException(
                    'Invalid value for {}'.format(item['name']))
