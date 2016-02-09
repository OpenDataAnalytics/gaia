import json
import os
import unittest
from zipfile import ZipFile
import shutil
from gaia.core import GaiaRequestParser

testfile_path = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../data/geoprocess')


class TestGaiaRequestParser(unittest.TestCase):
    """Tests for the GaiaRequestParser class"""

    def test_process_within(self):
        """Test Within process with nested Buffer process"""
        with open(os.path.join(testfile_path,
                               'within_nested_buffer_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('within',
                                    data=json_body).process
        process.compute()
        output = json.loads(process.output.data)
        with open(os.path.join(
                testfile_path,
                'within_nested_buffer_process_result.json')) as exp:
            expected_json = json.load(exp)
        self.assertIn('features', output)
        self.assertEquals(len(expected_json['features']),
                          len(output['features']))

    def test_process_subset_raster(self):
        """Test raster subset process with a raster file and geojson file"""
        with open(os.path.join(
                testfile_path, 'raster_subset_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
            process_json = json.loads(body_text)
        zipfile = ZipFile(os.path.join(testfile_path, '2states.zip'), 'r')
        process = GaiaRequestParser('subsetRaster',
                                    data=process_json).process
        try:
            zipfile.extract('2states.geojson', testfile_path)
            process.compute()
            self.assertEquals(type(process.output.data).__name__, 'Dataset')
            self.assertTrue(os.path.exists(process.output.file))
        finally:
            testfile = os.path.join(testfile_path, '2states.geojson')
            if os.path.exists(testfile):
                os.remove(testfile)
            if process.output and process.output.file:
                shutil.rmtree(os.path.dirname(process.output.file))

