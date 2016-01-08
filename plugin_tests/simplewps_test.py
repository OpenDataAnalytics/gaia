#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
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
from lxml import etree as et
from requests import Response
import requests
import xmltodict

# Need to set the environment variable before importing girder
os.environ['GIRDER_PORT'] = os.environ.get('GIRDER_TEST_PORT', '20200')
testfile_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'data/simplewps')


from tests import base


def setUpModule():
    """
    Enable the gaia plugin and start the server.
    """
    base.enabledPlugins.append('gaia')
    base.startServer(False)


def tearDownModule():
    """
    Stop the server.
    """
    base.stopServer()


def normalise_dict(d):
    """
    Recursively convert dict-like object (eg OrderedDict) into plain dict.
    Sorts list values.  Used for comparing XML
    """
    out = {}
    for k, v in dict(d).iteritems():
        if hasattr(v, 'iteritems'):
            out[k] = normalise_dict(v)
        elif isinstance(v, list):
            out[k] = []
            for item in sorted(v):
                if hasattr(item, 'iteritems'):
                    out[k].append(normalise_dict(item))
                else:
                    out[k].append(item)
        else:
            out[k] = v
    return out


def xml_compare(a, b):
    """
    Compares two XML documents (as string or etree)
    """
    a = normalise_dict(xmltodict.parse(a))
    b = normalise_dict(xmltodict.parse(b))
    return a == b


def mock_post(url, data=None, json=None, **kwargs):
    """
    Temporarily replace requests.post to return expect response from test files.
    """
    xml = et.fromstring(data)
    process = xml.find(
        './/ns2:Identifier', namespaces=xml.nsmap).text.replace(':', '_')
    filepath = os.path.join(testfile_path,
                            '{}.json'.format(process))

    with open(filepath, 'r') as infile:
        response = Response()
        response._content = infile.read()
        response.url = url
        response.json = response._content
        response.headers = {'content-type': 'application/json'}
        return response


class SimpleWpsTestCase(base.TestCase):
    """
    Test cases for the Gaia simplewms functionality
    """

    def setUp(self):
        """
        Set up the test case
        """
        super(SimpleWpsTestCase, self).setUp()

    def testVecQueryXml(self):
        """
        Test the generated XML body for a vec:Query WPS request
        """
        filepath = os.path.join(testfile_path, 'vec_Query.xml')
        path = '/simplewps/vec_Query'
        response = self.request(
            isJson=False,
            path=path,
            method='POST',
            body=json.dumps({
                "features": "geonode:ne_10m_admin_0_countries",
                "attribute": "the_geom",
                "filter": "ADM0_A3='PRI'",
                "return_xml": True
                }),
            type='application/json'
        )
        request_xml = response.body[0]
        with open(filepath) as testfile:
            expected_xml = testfile.read()

        self.assertTrue(xml_compare(request_xml, expected_xml))

    def testVecQueryProcess(self):
        """
        Test sending of a vec:Query WPS request using a mock response.
        """
        real_post = requests.post
        requests.post = mock_post
        filepath = os.path.join(testfile_path, 'vec_Query.json')
        path = '/simplewps/vec_Query'
        response = self.request(
            isJson=False,
            path=path,
            method='POST',
            body=json.dumps({
                "features": "geonode:ne_10m_admin_0_countries",
                "attribute": "the_geom",
                "filter": "ADM0_A3='PRI'"
                }),
            type='application/json'
        )
        with open(filepath) as testfile:
            expected_json = testfile.read()

        self.assertTrue(response, expected_json)
        requests.post = real_post

    def testVecClipXml(self):
        """
        Test the generated XML body for a vec:Clip WPS request
        """
        filepath = os.path.join(testfile_path, 'vec_Clip.xml')
        path = '/simplewps/vec_Clip'
        response = self.request(
            isJson=False,
            path=path,
            method='POST',
            body=json.dumps({
                "features": "geonode:gdacs_alerts",
                "clip": {
                    "features": "geonode:ne_10m_admin_0_countries",
                    "attribute": "the_geom",
                    "filter": "ADM0_A3='USA'",
                    },
                "return_xml": True
            }),
            type='application/json'
        )
        request_xml = response.body[0]
        with open(filepath) as testfile:
            expected_xml = testfile.read()
        self.assertTrue(xml_compare(request_xml, expected_xml))

    def testVecClipProcess(self):
        """
        Test sending of a vec:Clip WPS request using a mock response.
        """
        real_post = requests.post
        requests.post = mock_post
        filepath = os.path.join(testfile_path, 'vec_Clip.json')
        path = '/simplewps/vec_Clip'
        response = self.request(
            isJson=False,
            path=path,
            method='POST',
            body=json.dumps({
                "features": "geonode:gdacs_alerts",
                "clip": {
                    "features": "geonode:ne_10m_admin_0_countries",
                    "attribute": "the_geom",
                    "filter": "ADM0_A3='USA'",
                    }
            }),
            type='application/json'
        )
        with open(filepath) as testfile:
            expected_json = testfile.read()

        self.assertTrue(response, expected_json)
        requests.post = real_post

    def testGsCollectGeometriesXml(self):
        """
        Test the generated XML body for a gs:CollectGeometries WPS request
        """
        filepath = os.path.join(testfile_path, 'gs_CollectGeometries.xml')
        path = '/simplewps/gs_CollectGeometries'
        response = self.request(
            isJson=False,
            path=path,
            method='POST',
            body=json.dumps({
                    "features": "geonode:ne_10m_admin_0_countries",
                    "attribute": "the_geom",
                    "filter": "ADM0_A3='PRI'",
                    "return_xml": True
            }),
            type='application/json'
        )
        request_xml = response.body[0]
        with open(filepath) as testfile:
            expected_xml = testfile.read()
        self.assertTrue(xml_compare(request_xml, expected_xml))

    def testGsCollectGeometriesProcess(self):
        """
        Test sending of a gs:CollectGeometries WPS request
        using a mock response.
        """
        real_post = requests.post
        requests.post = mock_post
        filepath = os.path.join(testfile_path, 'gs_CollectGeometries.json')
        path = '/simplewps/gs_CollectGeometries'
        response = self.request(
            isJson=False,
            path=path,
            method='POST',
            body=json.dumps({
                    "features": "geonode:ne_10m_admin_0_countries",
                    "attribute": "the_geom",
                    "filter": "ADM0_A3='PRI'",
                    "return_xml": True
            }),
            type='application/json'
        )
        with open(filepath) as testfile:
            expected_json = testfile.read()

        self.assertTrue(response, expected_json)
        requests.post = real_post

    def testRasRasterZonalStatisticsXml(self):
        """
        Test the generated XML body for a ras"RasterZonalStatistics WPS request
        """
        filepath = os.path.join(testfile_path,
                                'ras_RasterZonalStatistics.xml')
        path = '/simplewps/ras_RasterZonalStatistics'
        response = self.request(
            isJson=False,
            path=path,
            method='POST',
            body=json.dumps({
                "return_xml": True,
                "data": "geonode:forecast_io_airtemp",
                "zones": {"type": "SimpleFeatureCollection",
                          "features": [
                              {"type": "Feature",
                               "geometry":
                                   {"type": "Polygon",
                                    "coordinates":
                                    [[[-108.80859373485288, 40.780541427145],
                                     [-108.80859373485288,37.09023979863171],
                                     [-101.4257812358789, 37.09023979863171],
                                     [-101.4257812358789, 40.780541427145],
                                     [-108.80859373485288, 40.780541427145]
                                     ]]}}],
                          "crs": {"type": "EPSG",
                                  "properties": {"code": "4326"}}}
                }),
            type='application/json'
        )
        request_xml = response.body[0]
        with open(filepath) as testfile:
            expected_xml = testfile.read()
        self.assertTrue(xml_compare(request_xml, expected_xml))

    def testRasRasterZonalStatisticsProcess(self):
        """
        Test sending of a ras:RasterZonalStatistics WPS request
        using a mock response.
        """
        real_post = requests.post
        requests.post = mock_post
        filepath = os.path.join(testfile_path,
                                'ras_RasterZonalStatistics.json')
        path = '/simplewps/ras_RasterZonalStatistics'
        response = self.request(
            isJson=False,
            path=path,
            method='POST',
            body=json.dumps({
                "return_xml": True,
                "data": "geonode:forecast_io_airtemp",
                "zones": {"type": "SimpleFeatureCollection",
                          "features": [
                              {"type": "Feature",
                               "geometry":
                                   {"type": "Polygon",
                                    "coordinates":
                                    [[[-108.80859373485288, 40.780541427145],
                                     [-108.80859373485288,37.09023979863171],
                                     [-101.4257812358789, 37.09023979863171],
                                     [-101.4257812358789, 40.780541427145],
                                     [-108.80859373485288, 40.780541427145]
                                     ]]}}],
                          "crs": {"type": "EPSG",
                                  "properties": {"code": "4326"}}}
                }),
            type='application/json'
        )
        with open(filepath) as testfile:
            expected_json = testfile.read()

        self.assertTrue(response, expected_json)
        requests.post = real_post
