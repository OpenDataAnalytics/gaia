"""Module defining python testing infrastructure."""

import os
import sys
from unittest import TestCase as _TestCase

try:
    import gaia as _gaia
except Exception:
    sys.path.append(os.path.abspath(os.path.join('..', '..')))
    import gaia as _gaia


class TestCase(_TestCase):

    """Base testing class extending unittest.TestCase."""

    # provide gaia import as a class variable to take care of import issues
    gaia = _gaia

    def data_path(self, filename=None):
        """Return an absolute path to a data file or directory."""
        pth = os.path.dirname(os.path.abspath(__file__))
        pth = os.path.join(os.path.dirname(pth), 'data')
        if filename is not None:
            pth = os.path.join(pth, filename)
        return pth
