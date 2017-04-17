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
import uuid
import numpy as np

import os
import fiona
import geopandas
import gdal
from sqlalchemy import create_engine, MetaData, Table, text
from geoalchemy2 import Geometry
try:
    import osr
except ImportError:
    from osgeo import osr
import gaia
import gaia.formats as formats
import gaia.types as types
from gaia import GaiaException, sqlengines, get_abspath
from gaia.inputs import GaiaIO, FileIO, UnsupportedFormatException
from gaia.filters import filter_pandas, filter_postgis
from gaia.geo.gdal_functions import gdal_reproject


class VectorMixin(object):
    """
    Mixin class for common vector data IO methods
    """
    def transform_data(self, outformat=None, epsg=None):
        """
        Transform the IO data into the requested format and projection if
        necessary.
        :param outformat: Output format
        :param epsg:
        :return:
        """
        out_data = geopandas.GeoDataFrame.copy(self.data)
        if epsg and str(self.get_epsg()) != epsg:
            out_data[out_data.geometry.name] = \
                self.data.geometry.to_crs(epsg=epsg)
            out_data.crs = fiona.crs.from_epsg(epsg)
        if outformat == formats.JSON and self.default_output in (
                formats.PANDAS, formats.JSON):
            out_json = out_data.to_json()
            if out_data.crs:
                gj = json.loads(out_json)
                gj["crs"] = {
                    "type": "name",
                    "properties": {
                        "name": out_data.crs["init"].upper()
                    }
                }
                return json.dumps(gj)
            else:
                return out_json
        elif outformat in [formats.PANDAS, None]:
            return out_data
        else:
            raise GaiaException("Format {} not supported".format(outformat))


class FeatureIO(GaiaIO, VectorMixin):
    """
    GeoJSON Feature Collection IO
    """
    #: Data type (vector or raster)
    type = types.VECTOR

    #: acceptable data format extensions
    format = formats.VECTOR

    #: Default output format
    default_output = formats.PANDAS

    def __init__(self,  features=None, **kwargs):
        """
        Create a FeatureIO object

        :param features: GeoJSON features/FeatureCollection
        :param kwargs:
        :return: FeatureIO object
        """
        super(FeatureIO, self).__init__(**kwargs)
        self.features = features

    def read(self, format=None, epsg=None):
        """
        Parse the FeatureIO.features and return as a GeoDataFrame or GeoJSON

        :param format: Format of output (default is GeoDataFrame)
        :param epsg: EPSG code of projection to reproject output to
        :return: Dataset in requested format
        """
        if not format:
            format = self.default_output
        if self.data is None and self.features:
            if type(self.features) == str:
                self.features = json.loads(self.features)
            features = self.features

            if 'type' in features and features['type'] == 'FeatureCollection':
                self.data = geopandas.GeoDataFrame.from_features(
                    self.features['features'])
            else:
                self.data = geopandas.GeoDataFrame.from_features(features)
        if not self.data.crs:
            if hasattr(self, 'crs'):
                self.data.crs = self.crs
            else:
                self.get_epsg()

        return self.transform_data(outformat=format, epsg=epsg)

    def delete(self):
        """
        Reset the IO data to None
        """
        self.data = None


class VectorFileIO(FileIO, VectorMixin):
    """
    Read and write vector file data (such as GeoJSON)
    Data will be read into a geopandas dataframe.
    """

    #: Data type (vector or raster)
    type = types.VECTOR

    #: acceptable data format extensions
    format = formats.VECTOR

    #: Default output format
    default_output = formats.PANDAS

    #: Optional arguments
    optional_args = {
        'filters': list
    }

    def read(self, format=None, epsg=None):
        """
        Read vector data from a file (JSON, Shapefile, etc)

        :param format: Format to return data in (default is GeoDataFrame)
        :param epsg: EPSG code to reproject data to
        :return: Data in requested format (GeoDataFrame, GeoJSON)
        """
        if not format:
            format = self.default_output
        if self.ext not in formats.VECTOR:
            raise UnsupportedFormatException(
                "Only the following vector formats are supported: {}".format(
                    ','.join(formats.VECTOR)
                )
            )
        if self.data is None:
            self.data = geopandas.read_file(self.uri)
            if self.filters:
                self.filter_data()
        return self.transform_data(format, epsg)

    def write(self, filename=None, as_type='json'):
        """
        Write data (assumed geopandas) to geojson or shapefile

        :param filename: Base filename
        :param as_type: shapefile or json
        :return: location of file
        """
        if not filename:
            filename = self.uri
        self.create_output_dir(filename)
        if as_type == 'json':
            with open(filename, 'w') as outfile:
                outfile.write(self.transform_data(outformat=formats.JSON))
        elif as_type == 'shapefile':
            self.data.to_file(filename)
        else:
            raise NotImplementedError('{} not a valid type'.format(as_type))
        return self.uri

    def filter_data(self):
        """
        Apply filters to the dataset
        """
        self.data = filter_pandas(self.data, self.filters)


class RasterFileIO(FileIO):
    """Read and write raster data (GeoTIFF)"""

    #: Data type (vector or raster)
    type = types.RASTER

    #: acceptable data format extensions
    format = formats.RASTER

    #: Default output format
    default_output = formats.RASTER

    def raster_to_numpy_ar(raster_data):
        """
        Convert raster output to numpy array output

        :param raster_data: Original raster output dataset
        :return: Converted numpy array dataset
        """
        bands = raster_data.RasterCount
        nrow = raster_data.RasterYSize
        ncol = raster_data.RasterXSize
        out_data_ar = np.zeros([bands, nrow, ncol])

        for i in range(bands):
            srcband = raster_data.GetRasterBand(i+1)
            if srcband is None:
                continue
            srcband_ar = np.array(srcband.ReadAsArray())
            out_data_ar[i, :, :] = srcband_ar

        return out_data_ar

    def read(self, as_numpy_array=False, epsg=None):
        """
        Read data from a raster dataset

        :param epsg: EPSG code to reproject data to
        :param as_numpy_array: Output data as numpy  (default is raster)
        :return: GDAL Dataset
        """
        if self.ext not in formats.RASTER:
            raise UnsupportedFormatException(
                "Only the following raster formats are supported: {}".format(
                    ','.join(formats.RASTER)
                )
            )
        self.basename = os.path.basename(self.uri)
        if not self.data:
            self.data = gdal.Open(self.uri)
        out_data = self.data
        if epsg and self.get_epsg() != epsg:
            out_data = reproject(self.data, epsg)

        if as_numpy_array:
            return self.raster_to_numpy_ar(out_data)
        else:
            return out_data


class ProcessIO(GaiaIO):
    """IO for nested GaiaProcess objects"""

    #: Data type
    type = types.PROCESS

    #: Optional arguments
    optional_args = {
        'parent': uuid.UUID
    }

    def __init__(self, process=None, parent=None, **kwargs):
        """
        Create an IO object containing a GaiaProcess to run

        :param process: GaiaProcess to run
        :param parent: Parent process id if any
        :param kwargs:
        """
        super(ProcessIO, self).__init__(**kwargs)
        self.process = process
        self.parent = parent
        self.default_output = process.default_output

    def get_epsg(self):
        """
        Return the EPSG code of the dataset
        """
        if hasattr(self.process, 'output') and self.process.output.data \
                is not None:
            return self.process.output.get_epsg()
        else:
            return self.process.inputs[0].get_epsg()

    def read(self, epsg=None):
        """
        Return the process output dataset

        :param epsg: EPSG code to reproject data to
        :return: Output dataset
        """
        if self.data is None:
            self.process.compute()
            self.data = self.process.output.data
        out_data = self.data
        if epsg and self.get_epsg() != epsg:
            out_data = reproject(self.data, epsg)
        return out_data


class PostgisIO(GaiaIO, VectorMixin):
    """Read PostGIS data"""

    #: Data type (vector or raster)
    type = types.VECTOR

    #: acceptable data format extensions
    format = formats.VECTOR

    #: Default output format
    default_output = formats.JSON

    hostname = None
    dbname = None
    user = None
    password = None
    table = None
    columns = []
    filters = None
    geom_column = 'the_geom'
    epsg = None
    engine = None
    meta = None
    table_obj = None

    def __init__(self, table, **kwargs):
        """
        Instantiate a PostgisIO object for querying a PostGIS table

        :param table: PostgreSQL table name
        :param kwargs: Optional connection arguments,
        obtained from config if not present
        """
        super(PostgisIO, self).__init__(**kwargs)
        self.table = table
        self.host = kwargs.get('host') or gaia.config['gaia_postgis']['host']
        self.dbname = kwargs.get(
            'dbname') or gaia.config['gaia_postgis']['dbname']
        self.user = kwargs.get('user') or gaia.config['gaia_postgis']['user']
        self.password = kwargs.get(
            'password') or gaia.config['gaia_postgis']['password']
        self.engine = self.get_engine(self.get_connection_string())
        self.get_table_info()
        self.verify()

    def get_engine(self, connection_string):
        """
        Create and return a SQLAlchemy engine object

        :param connection_string: Database connection string
        :return: SQLAlchemy Engine object
        """
        if connection_string not in sqlengines:
            sqlengines[connection_string] = create_engine(
                self.get_connection_string())
        return sqlengines[connection_string]

    def verify(self):
        """
        Make sure that all PostgisIO columns exist in the actual table
        """
        for col in self.columns:
            if col not in self.table_obj.columns.keys():
                raise Exception('{} column not found in {}'.format(
                    col, self.table_obj))

    def get_connection_string(self):
        """
        Get connection string based on host, dbname, username, password

        :return: Postgres connection string for SQLAlchemy
        """
        auth = ''
        if self.user:
            auth = self.user
        if self.password:
            auth = auth + ':' + self.password
        if auth:
            auth += '@'
        conn_string = 'postgresql://{auth}{host}/{dbname}'.format(
            auth=auth, host=self.host, dbname=self.dbname)

        return conn_string

    def get_epsg(self):
        """
        Get the EPSG code of the data

        :return: EPSG code
        """
        return self.epsg

    def get_table_info(self):
        """
        Use SQLALchemy reflection to gather data on the table, including the
        geometry column, geometry type, and EPSG code, and assign to the
        PostgisIO object's attributes.
        """
        epsg = None
        meta = MetaData()
        table_obj = Table(self.table, meta,
                          autoload=True, autoload_with=self.engine)
        if not self.columns:
            self.columns = table_obj.columns.keys()
        geo_cols = [(col.name, col.type) for col in table_obj.columns
                    if hasattr(col.type, 'srid')]
        if geo_cols:
            geo_col = geo_cols[0]
            self.geom_column = geo_col[0]
            geo_obj = geo_col[1]
            if self.geom_column not in self.columns:
                self.columns.append(self.geom_column)
            if hasattr(geo_obj, 'srid'):
                epsg = geo_obj.srid
                if epsg == -1:
                    epsg = 4326
            if hasattr(geo_obj, 'geometry_type'):
                self.geometry_type = geo_obj.geometry_type

        self.epsg = epsg
        self.table_obj = table_obj
        self.meta = meta

    def get_geometry_type(self):
        """
        Get the geometry type of the data

        :return: Geometry type
        """
        return self.geometry_type

    def get_query(self):
        """
        Formulate a query string and parameter list based on the
        table name, columns, and filter

        :return: Query string
        """
        columns = ','.join(['"{}"'.format(x) for x in self.columns])
        query = 'SELECT {} FROM "{}"'.format(columns, self.table)
        filter_params = []
        if self.filters:
            filter_sql, filter_params = filter_postgis(self.filters)
            query += ' WHERE {}'.format(filter_sql)
        query += ';'
        return str(text(query)), filter_params

    def read(self, format=None, epsg=None):
        """
        Load the table data into a GeoDataFrame, and return as a GeoDataFrame
        or GeoJSON object

        :param format: Output format (default is GeoDataFrame)
        :param epsg: EPSG code to reproject the data to
        :return: data in requested format
        """
        if self.data is None:
            query, params = self.get_query()
            self.data = df_from_postgis(self.engine, query, params,
                                        self.geom_column, self.epsg)
        return self.transform_data(outformat=format, epsg=epsg)


def df_from_postgis(engine, query, params, geocolumn, epsg):
    """
    Run a PostGIS query and return results as a GeoDataFrame

    :param engine: SQLAlchemy database connection engine
    :param query: Query to run
    :param params: Query parameter list
    :param geocolumn: Geometry column of query
    :param epsg: EPSG code of geometry output
    :return: GeoDataFrame
    """
    data = geopandas.GeoDataFrame.from_postgis(
        query,
        engine,
        geom_col=geocolumn,
        crs={'init': 'epsg:{}'.format(epsg)},
        params=params)
    return data


def reproject(dataset, epsg):
    """
    Reproject a dataset to the specified EPSG code

    :param dataset: Dataset to reproject
    :param epsg: EPSG code to reproject to
    :return: Reprojected data
    """
    dataclass = dataset.__class__.__name__
    # Run appropriate reprojection method
    if dataclass == 'GeoDataFrame':
        repro = geopandas.GeoDataFrame.copy(dataclass)
        repro[repro.geometry.name] = repro.geometry.to_crs(epsg=epsg)
        repro.crs = fiona.crs.from_epsg(epsg)
    elif dataclass == 'Dataset':
        repro = gdal_reproject(dataset, '', epsg=epsg)
    return repro
