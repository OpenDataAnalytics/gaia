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
import gzip
import json
import os
from xml.etree import ElementTree as et

from httmock import urlmatch, HTTMock, response as httmockresponse

# Need to set the environment variable before importing girder
os.environ['GIRDER_PORT'] = os.environ.get('GIRDER_TEST_PORT', '20200')
testfile_path = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../tests/data')

from tests import base

@urlmatch(netloc=r'.*')
def wms_gc_mock(url, request):
    pluginTestDir = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(pluginTestDir, 'data', 'wms_capabilities.xml.gz')
    with gzip.open(filepath, 'r') as get_capabilities_file:
        content = get_capabilities_file.read()
        headers = {
            'content-length': len(content),
            'content-type': 'application/xml'
        }
        return httmockresponse(200, content, headers, request=request)

@urlmatch(netloc=r'.*')
def wms_gm_mock(url, request):
    pluginTestDir = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(pluginTestDir, 'data', 'wms_getmap.png')
    with open(filepath, 'rb') as tile_image:
        content = tile_image.read()
        headers = {
            'content-length': len(content),
            'content-type': 'image/png'
        }
        return httmockresponse(200, content, headers, request=request)

@urlmatch(netloc=r'.*')
def wfs_gf_mock(url, request):
    pluginTestDir = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(pluginTestDir, 'data', 'wfs_getfeature.xml')
    with open(filepath, 'rb') as tile_image:
        content = tile_image.read()
        headers = {
            'content-length': len(content),
            'content-type': 'application/xml'
        }
        return httmockresponse(200, content, headers, request=request)


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


class GeoprocessTestCase(base.TestCase):
    """
    Test cases for the Gaia geoprocess functionality
    """

    def setUp(self):
        """
        Set up the test case
        """
        super(GeoprocessTestCase, self).setUp()
        """
         TODO: Figure out the best way of making Gaia core functionality
         independent of Girder while still being able to load it as a plugin.
         For now, this path hack does the trick.
        """

    def testGeoserverGetCapabilities(self):
        """
        The following request should return a GetCapabilities document
        """
        with HTTMock(wms_gc_mock):
            response = self.request(
                isJson=False,
                path='/geo/wms',
                prefix='',
                params={'service': 'WMS',
                        'request': 'GetCapabilities',
                        'version': '1.1.1'},
                method='GET'
            )
        caps = et.fromstring(response.body[0])
        self.assertEquals(caps.tag, 'WMT_MS_Capabilities')
        self.assertStatusOk(response)

    def testGeoserverGetMap(self):
        """
        The following request should return a map tile
        """
        with HTTMock(wms_gm_mock):
            response = self.request(
                isJson=False,
                path='/geo/wms',
                prefix='',
                params={'SERVICE': 'WMS',
                        'REQUEST': 'GetMap',
                        'LAYERS': 'brazil_10m_adm',
                        'TRANSPARENT': 'TRUE',
                        'FORMAT': 'image/png',
                        'TILED': 'true',
                        'SRS': 'EPSG:3857',
                        'BBOX': '-10018754.17,-5009377.085,-5009377.085,0',
                        'WIDTH': 256,
                        'HEIGHT': 256
                        },
                method='GET'
            )
        self.assertStatusOk(response)
        self.assertEquals(response.headers['content-type'], 'image/png')

    def testGeoserverWfsGetFeature(self):
        """
        The following request should return a map tile
        """
        with HTTMock(wfs_gf_mock):
            response = self.request(
                isJson=False,
                path='/geo/wfs',
                prefix='',
                params={'request': 'GetFeature',
                        'outputFormat': 'GML2',
                        'typeName': 'topp:states',
                        'version': '1.0.0',
                        'FILTER': '<Filter xmlns="http://www.opengis.net/ogc"'
                                  'xmlns:gml="http://www.opengis.net/gml">'
                                  '<Intersects>'
                                  '<PropertyName>the_geom</PropertyName>'
                                  '<gml:Point srsName="EPSG:4326">'
                                  '<gml:coordinates>-74.817265,40.5296504'
                                  '</gml:coordinates></gml:Point></Intersects>'
                                  '</Filter>'},
                method='GET'
            )
        self.assertStatusOk(response)
        caps = et.fromstring(response.body[0])
        self.assertEquals(caps.tag,
                          '{http://www.opengis.net/wfs}FeatureCollection')

    def testGeoserverREST(self):
        """
        The following request should create a new empty layer,
        and a blank response with ok status.
        """
        pluginTestDir = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(pluginTestDir, 'data', 'rest_featuretype.xml')
        with open(filepath, 'r') as inf:
            body_xml = inf.read()
        with HTTMock(wms_gm_mock):
            response = self.request(
                isJson=False,
                path='/geo/rest/workspaces/geonode/datastores/foo/featuretypes',
                prefix='',
                body=body_xml,
                additionalHeaders=[('Content-Type', 'application/xml')],
                method='POST'
            )
        self.assertStatusOk(response)
