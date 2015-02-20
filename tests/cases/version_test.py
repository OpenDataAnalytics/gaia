import re

from base import TestCase


class VersionTest(TestCase):

    """Contains tests of the package version string."""

    def test_version_present(self):
        """Make sure the version is defined."""
        self.assertIn('version', self.gaia.__dict__)

    def test_version_format(self):
        """Make sure the version is formatted correctly."""
        r = re.compile(r'^\d\.\d\.\d(-[^-.]+)?$')
        self.assertRegexpMatches(self.gaia.version, r)
