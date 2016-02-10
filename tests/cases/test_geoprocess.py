import json
import os
import unittest
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

    def test_process_intersects(self):
        """Test Intersects process"""
        with open(os.path.join(testfile_path,
                               'intersects_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('intersects',
                                    data=json_body).process
        process.compute()
        output = json.loads(process.output.data)
        with open(os.path.join(
                testfile_path,
                'intersects_process_results.json')) as exp:
            expected_json = json.load(exp)
        self.assertIn('features', output)
        self.assertEquals(len(expected_json['features']),
                          len(output['features']))

    def test_process_difference(self):
        """Test Difference Process"""
        with open(os.path.join(testfile_path,
                               'difference_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('difference',
                                    data=json_body).process
        process.compute()
        output = json.loads(process.output.data)
        with open(os.path.join(
                testfile_path,
                'difference_process_results.json')) as exp:
            expected_json = json.load(exp)
        self.assertIn('features', output)
        self.assertEquals(len(expected_json['features']),
                          len(output['features']))

    def test_process_controid(self):
        """Test Centroid Process"""
        with open(os.path.join(testfile_path,
                               'centroid_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('centroid',
                                    data=json_body).process
        process.compute()
        output = json.loads(process.output.data)
        with open(os.path.join(
                testfile_path,
                'centroid_process_results.json')) as exp:
            expected_json = json.load(exp)
        self.assertIn('features', output)
        self.assertEquals(len(expected_json['features']),
                          len(output['features']))

    def test_process_distance(self):
        """Test Distance Process"""
        with open(os.path.join(testfile_path,
                               'distance_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('distance',
                                    data=json_body).process
        process.compute()
        output = json.loads(process.output.data)
        with open(os.path.join(
                testfile_path,
                'distance_process_results.json')) as exp:
            expected_json = json.load(exp)
        self.assertIn('features', output)
        self.assertEquals(len(expected_json['features']),
                          len(output['features']))