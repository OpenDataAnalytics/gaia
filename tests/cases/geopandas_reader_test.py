from base import TestCase
from gaia.pandas import GeopandasReader


class GeopandasReaderTest(TestCase):

    """Test the geopandas file reader."""

    def test_read_geojson(self):
        """Validate the contents of a simple geojson file."""
        reader = GeopandasReader()

        reader.file_name = self.data_path('geopoints.json')
        data = reader.get_output_data()

        self.assertTrue('elevation' in data)
        self.assertTrue('geometry' in data)
        self.assertTrue(data.geometry[0].geom_type == 'Point')
