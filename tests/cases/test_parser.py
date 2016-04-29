#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc. and Epidemico Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################
import json
import os
import unittest
from zipfile import ZipFile
from gaia import formats
from gaia.parser import deserialize
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
        process = json.loads(body_text, object_hook=deserialize)
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
        process = json.loads(body_text, object_hook=deserialize)
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

    def test_process_disjoint(self):
        """Test Difference Process"""
        with open(os.path.join(testfile_path,
                               'difference_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        process = json.loads(body_text, object_hook=deserialize)
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
        process = json.loads(body_text, object_hook=deserialize)
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
        process = json.loads(body_text, object_hook=deserialize)
        try:
            print 'process ', process
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
        process = json.loads(body_text, object_hook=deserialize)
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
            process = json.loads(body_text, object_hook=deserialize)
        zipfile = ZipFile(os.path.join(testfile_path, '2states.zip'), 'r')

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
                process = json.load(inf, object_hook=deserialize)

        print 'inf ', inf
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
        process = json.loads(body_text, object_hook=deserialize)
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
        process = json.loads(body_text, object_hook=deserialize)
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
        process = json.loads(body_text, object_hook=deserialize)
        try:
            process.compute()
            output = process.output.read(format=formats.WEIGHT)
            exp = pysal.open(os.path.join(testfile_path,
                                          'weight_process_result.gal'), 'r')
            expected_w = exp.read()
            exp.close()
            self.assertEquals(expected_w.n,
                              output.n)
            self.assertIsNotNone(process.id)
            self.assertIn(process.id, process.output.uri)
        finally:
            if process:
                process.purge()
