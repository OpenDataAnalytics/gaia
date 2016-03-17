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
import codecs
import glob
import json
import unittest
import os
import sqlalchemy
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch
from sqlalchemy import create_engine, text
import gaia.geo
import gaia.core
import gaia.formats as formats
from gaia.inputs import PostgisIO

base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))


def get_engine(self, connection_string):
    if connection_string not in gaia.core.sqlengines:
        gaia.core.sqlengines[connection_string] = create_engine(
            self.get_connection_string(), poolclass=NullPool)
    return gaia.core.sqlengines[connection_string]


class TestPostGisDB(unittest.TestCase):

    @classmethod
    def get_connection(cls, dbname=''):
        auth = cls.user
        if cls.password:
            auth = cls.user + ":" + cls.password
        auth += '@'

        conn_string = 'postgresql://{auth}{host}{dbname}'.format(
            auth=auth,
            host=cls.host,
            dbname='/' + dbname
        )
        engine = sqlalchemy.create_engine(conn_string)
        return engine.connect()

    @classmethod
    def setUpClass(cls):
        config_file = os.path.join(base_dir, '../conf/test.local.cfg')
        config = gaia.core.get_config(config_file)
        cls.user = config['gaia_postgis']['user']
        cls.password = config['gaia_postgis']['password']
        cls.host = config['gaia_postgis']['host']
        cls.dbname = config['gaia_postgis']['dbname']

        try:
            connection = cls.get_connection()
        except OperationalError:
            raise unittest.SkipTest()

        iso_level = connection.connection.connection.isolation_level
        connection.connection.connection.set_isolation_level(0)
        try:
            connection.execute("DROP DATABASE IF EXISTS {}".format(cls.dbname))
            connection.execute("CREATE DATABASE {}".format(cls.dbname))
            connection.close()
            connection.engine.dispose()
            connection = cls.get_connection(cls.dbname)
            connection.execute(text("CREATE EXTENSION postgis;").
                               execution_options(autocommit=True))
            for sqlfile in glob.glob(os.path.join(base_dir, "../data/*.sql")):
                with codecs.open(sqlfile, "r", "utf-8") as inf:
                    sql = inf.read()
                    connection.execute(
                        text(sql).execution_options(autocommit=True))
        finally:
            connection.connection.connection.set_isolation_level(iso_level)
            connection.close()
            connection.engine.dispose()

    @classmethod
    def tearDownClass(cls):
        connection = cls.get_connection()
        iso_level = connection.connection.connection.isolation_level
        connection.connection.connection.set_isolation_level(0)
        try:
            connection.execute("DROP DATABASE IF EXISTS {}".format(cls.dbname))
        finally:
            connection.connection.connection.set_isolation_level(iso_level)
            connection.close()
            connection.engine.dispose()

    @patch('gaia.inputs.PostgisIO.get_engine', get_engine)
    def test_area_process(self):
        pgio = PostgisIO(table='baghdad_districts',
                         host=self.host,
                         dbname=self.dbname,
                         user=self.user,
                         password=self.password,
                         filters=[('nname', 'LIKE', 'B%')])
        process = gaia.geo.AreaProcess(inputs=[pgio])
        try:
            process.compute()
            with open(os.path.join(
                    base_dir,
                    '../data/area_process_results.json')) as exp:
                expected_json = json.load(exp)
            actual_json = json.loads(process.output.read(format=formats.JSON))
            self.assertEquals(len(expected_json['features']),
                              len(actual_json['features']))
        finally:
            if process:
                process.purge()

    @patch('gaia.inputs.PostgisIO.get_engine', get_engine)
    def test_within(self):
        """
        Test WithinProcess for PostGIS inputs
        """
        pg_hospitals = PostgisIO(table='iraq_hospitals',
                                 host=self.host,
                                 dbname=self.dbname,
                                 user=self.user,
                                 password=self.password)
        pg_districts = PostgisIO(table='baghdad_districts',
                                 host=self.host,
                                 dbname=self.dbname,
                                 user=self.user,
                                 password=self.password,
                                 filters=[('nname', 'LIKE', 'A%')])
        process = gaia.geo.WithinProcess(inputs=[pg_hospitals, pg_districts])
        try:
            process.compute()
            with open(os.path.join(
                    base_dir,
                    '../data/within_process_results.json')) as exp:
                expected_json = json.load(exp)
            actual_json = json.loads(process.output.read(format=formats.JSON))
            self.assertEquals(len(expected_json['features']),
                              len(actual_json['features']))
        finally:
            if process:
                process.purge()
