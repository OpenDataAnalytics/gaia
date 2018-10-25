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
import os
import json
import unittest
from zipfile import ZipFile
import gaia
from gaia.preprocess import crop

base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))
testfile_path = os.path.join(base_dir, '../data')


class TestCreateAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_file = os.path.join(base_dir, '../../gaia/conf/gaia.cfg')
        gaia.get_config(config_file)

    def test_create_api(self):
        """
        Test cropping (within process) for vector inputs
        """
        path1 = os.path.join(testfile_path, 'iraq_hospitals.geojson')
        path2 = os.path.join(testfile_path, 'baghdad_districts.geojson')

        data1 = gaia.create(path1)
        data2 = gaia.create(path2)

        output = crop(data1, data2)

        self.assertEqual(len(output.get_data()), 19)
