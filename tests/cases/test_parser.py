import json
import os
import unittest
from zipfile import ZipFile
import shutil
from gaia import formats
from gaia.parser import GaiaRequestParser

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
        try:
            process.compute()
            output = json.loads(process.output.read(format=formats.JSON))
            with open(os.path.join(
                    testfile_path,
                    'within_nested_buffer_process_result.json')) as exp:
                expected_json = json.load(exp)
            self.assertIn('features', output)
            self.assertEquals(len(expected_json['features']),
                              len(output['features']))
            self.assertIsNotNone(process.id)
            self.assertIn(process.id, process.output.uri)
        finally:
            pass
            if process:
                process.purge()

    def test_process_intersects(self):
        """Test Intersects process"""
        with open(os.path.join(testfile_path,
                               'intersects_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('intersects',
                                    data=json_body).process
        try:
            process.compute()
            output = json.loads(process.output.read(format=formats.JSON))
            with open(os.path.join(
                    testfile_path,
                    'intersects_process_results.json')) as exp:
                expected_json = json.load(exp)
            self.assertIn('features', output)
            self.assertEquals(len(expected_json['features']),
                              len(output['features']))
        finally:
            pass
            if process:
                process.purge()

    def test_process_difference(self):
        """Test Difference Process"""
        with open(os.path.join(testfile_path,
                               'difference_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('difference',
                                    data=json_body).process
        try:
            process.compute()
            output = json.loads(process.output.read(format=formats.JSON))
            with open(os.path.join(
                    testfile_path,
                    'difference_process_results.json')) as exp:
                expected_json = json.load(exp)
            self.assertIn('features', output)
            self.assertEquals(len(expected_json['features']),
                              len(output['features']))
        finally:
            pass
            if process:
                process.purge()

    def test_process_union(self):
        """Test Union Process"""
        with open(os.path.join(testfile_path,
                               'union_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('union',
                                    data=json_body).process
        try:
            process.compute()
            output = json.loads(process.output.read(format=formats.JSON))
            with open(os.path.join(
                    testfile_path,
                    'union_process_results.json')) as exp:
                expected_json = json.load(exp)
            self.assertIn('features', output)
            self.assertEquals(len(expected_json['features']),
                              len(output['features']))
        finally:
            pass
            if process:
                process.purge()


    def test_process_centroid(self):
        """Test Centroid Process"""
        with open(os.path.join(testfile_path,
                               'centroid_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('centroid',
                                    data=json_body).process
        try:
            process.compute()
            output = json.loads(process.output.read(format=formats.JSON))
            with open(os.path.join(
                    testfile_path,
                    'centroid_process_results.json')) as exp:
                expected_json = json.load(exp)
            self.assertIn('features', output)
            self.assertEquals(len(expected_json['features']),
                              len(output['features']))
        finally:
            pass
            if process:
                process.purge()

    def test_process_distance(self):
        """Test Distance Process"""
        with open(os.path.join(testfile_path,
                               'distance_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('distance',
                                    data=json_body).process
        try:
            process.compute()
            output = json.loads(process.output.read(format=formats.JSON))
            with open(os.path.join(
                    testfile_path,
                    'distance_process_results.json')) as exp:
                expected_json = json.load(exp)
            self.assertIn('features', output)
            self.assertEquals(len(expected_json['features']),
                              len(output['features']))
        finally:
            pass
            if process:
                process.purge()

    def test_process_subset_raster(self):
        """Test raster subset process with a raster file and geojson file"""
        with open(os.path.join(
                testfile_path, 'raster_subset_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
            process_json = json.loads(body_text)
        zipfile = ZipFile(os.path.join(testfile_path, '2states.zip'), 'r')
        process = GaiaRequestParser('subset',
                                    data=process_json).process
        try:
            zipfile.extract('2states.geojson', testfile_path)
            process.compute()
            self.assertEquals(type(process.output.data).__name__, 'Dataset')
            self.assertTrue(os.path.exists(process.output.uri))
            self.assertIsNotNone(process.id)
            self.assertIn(process.id, process.output.uri)
        finally:
            testfile = os.path.join(testfile_path, '2states.geojson')
            if os.path.exists(testfile):
                os.remove(testfile)
            if process:
                process.purge()

