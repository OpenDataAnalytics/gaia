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

# Need to set the environment variable before importing girder
os.environ['GIRDER_PORT'] = os.environ.get('GIRDER_TEST_PORT', '20200')
testfile_path = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../tests/data')


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

    def testFakeProcess(self):
        """
        Test the generated XML body for a vec:Query WPS request
        """
        with open(os.path.join(testfile_path,
                               'within_nested_buffer_process.json')) as inf:
            body_text = inf.read().replace('{basepath}', testfile_path)
        path = '/geoprocess/within'
        response = self.request(
            isJson=False,
            path=path,
            method='POST',
            body=body_text,
            type='application/json'
        )
        output = json.loads(response.body[0])
        with open(os.path.join(
                testfile_path,
                'within_nested_buffer_process_result.json')) as exp:
            expected_json = json.load(exp)
        self.assertIn('features', output)
        self.assertEquals(len(expected_json['features']),
                          len(output['features']))
