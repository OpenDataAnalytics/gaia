from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

from gaia import GaiaException
from gaia.girder_data import GirderDataObject
from gaia.process_registry import register_process


@register_process('crop')
def compute_subset_girder(inputs=[], args=[]):
    """
    Runs the subset computation on girder
    """
    print('inputs: ', inputs)
    print('args:', args)

    # Verify that all inputs are girder objects
    for dataset in inputs:
        assert isinstance(dataset,GirderDataObject), 'Some input datasets are NOT girder objects'


    outputDataObject = GirderDataObject(None, 'type_undefined', 'id_undefinded')
    return outputDataObject
