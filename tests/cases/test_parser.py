import json
import os
import unittest
from zipfile import ZipFile
from gaia import formats
from gaia.parser import GaiaRequestParser
import pysal

testfile_path = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../data')


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

    def test_process_within_featureio(self):
        """Test Within process with nested Buffer process using geojson input"""
        with open(os.path.join(
                testfile_path,
                'within_nested_buffer_features_process.json')) as inf:
            json_body = json.load(inf)
        process = GaiaRequestParser('within',
                                    data=json_body).process
        try:
            process.compute()
            output = json.loads(process.output.read(format=formats.JSON))
            with open(os.path.join(
                    testfile_path,
                    'within_nested_buffer_features_process_result.json')) as gj:
                expected_json = json.load(gj)
            self.assertIn('features', output)
            self.assertEquals(len(expected_json['features']),
                              len(output['features']))
            self.assertIsNotNone(process.id)
            self.assertIn(process.id, process.output.uri)
        finally:
            if process:
                process.purge()

    def test_process_cluster(self):
        """Test Cluster Process"""
        with open(os.path.join(testfile_path,
                               'cluster_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('cluster',
                                    data=json_body).process
        try:
            process.compute()
            output = json.loads(process.output.read(format=formats.JSON))
            with open(os.path.join(
                    testfile_path,
                    'cluster_process_results.json')) as gj:
                expected_json = json.load(gj)
            self.assertIn('features', output)
            self.assertEquals(len(expected_json['features']),
                              len(output['features']))
            self.assertIsNotNone(process.id)
            self.assertIn(process.id, process.output.uri)
        finally:
            if process:
                process.purge()

    def test_process_autocorrelation(self):
        """Test Autocorrelation Process"""
        with open(os.path.join(testfile_path,
                               'autocorrelation_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('autocorrelation',
                                    data=json_body).process
        try:
            process.compute()
            output = process.output.read(format=formats.JSON)
            with open(os.path.join(
                    testfile_path,
                    'autocorrelation_process_results.json')) as exp:
                expected_json = json.load(exp)
            self.assertIn('I', output)
            self.assertEquals(expected_json['I'],
                              output['I'])
            self.assertIsNotNone(process.id)
            self.assertIn(process.id, process.output.uri)
        finally:
            if process:
                process.purge()

    def test_process_weight(self):
        """Test Weight Process"""
        with open(os.path.join(testfile_path,
                               'weight_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        json_body = json.loads(body_text)
        process = GaiaRequestParser('weight',
                                    data=json_body).process
        try:
            process.compute()
            output = process.output.read(format=formats.WEIGHT)
            exp = pysal.open(os.path.join(testfile_path, 'weight_process_result.gal'), 'r')
            expected_w = exp.read()
            exp.close()
            self.assertEquals(expected_w.n,
                              output.n)
            self.assertIsNotNone(process.id)
            self.assertIn(process.id, process.output.uri)
        finally:
            if process:
                process.purge()