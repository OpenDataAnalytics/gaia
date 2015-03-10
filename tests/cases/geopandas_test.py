import os

import matplotlib
matplotlib.use('Agg')  # noqa

from base import TestCase
from gaia.pandas import GeopandasReader, GeopandasPlot


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


class GeopandasPlotTest(TestCase):

    """Test the geopandas plotter."""

    def setUp(self):  # noqa
        """Read a small geojson file."""
        TestCase.setUp(self)
        self.reader = GeopandasReader()
        self.reader.file_name = self.data_path('geopoints.json')

    def _plot_geojson(self, ext):
        """Read a small geojson file and save a plot."""

        plotter = GeopandasPlot()
        plotter.set_input(port=self.reader.get_output())
        plotter.file_name = self.output_path('geopoints.' + ext)

        plotter.run()
        self.assertTrue(os.path.exists(plotter.file_name))

    def test_plot_geojson_png(self):
        """Create a png image."""
        self._plot_geojson('png')

    def test_plot_geojson_pdf(self):
        """Create a pdf image."""
        self._plot_geojson('pdf')

    def test_plot_geojson_jpg(self):
        """Create a jpg image."""
        self._plot_geojson('jpg')
