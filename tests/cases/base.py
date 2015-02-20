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
