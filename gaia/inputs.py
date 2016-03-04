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
import errno
import fiona
import geopandas
import gdal
import shutil
from gaia.gdal_functions import gdal_reproject
from sqlalchemy import create_engine, MetaData, Table, text

try:
    import osr
except ImportError:
    from osgeo import osr
import gaia.formats as formats
from gaia.core import GaiaException, config
from gaia.filters import filter_pandas, filter_postgis


class MissingParameterError(GaiaException):
    """Raise when a required parameter is missing"""
    pass


class MissingDataException(GaiaException):
    """Raise when required data is missing"""
    pass


class UnsupportedFormatException(GaiaException):
    """Raise when an unsupported data format is used"""
    pass


class GaiaIO(object):
    """Abstract IO class for importing/exporting data from a certain source"""
    data = None
    filters = None
    default_output = None

    def __init__(self, **kwargs):
        """
        Create a GaiaIO object, assigning attributes based on kwargs
        :param kwargs:
        :return:
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

    def read(self, *args, **kwargs):
        """
        Abstract class for reading data, not implemented here
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def write(self, *args, **kwargs):
        """
        Abstract class for writing data
        :param args:
        :param kwargs:
        :return:
        """
        pass

    def create_output_dir(self, filepath):
        """
        Create an output directory if it doesn't exist
        :param filepath: Directory to create
        :return:
        """
        if not os.path.exists(os.path.dirname(filepath)):
            try:
                os.makedirs(os.path.dirname(filepath))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise

    def get_epsg(self):
        """
        Get the EPSG code of the data
        :return: EPSG code (integer)
        """
        if self.data is None:
            self.read()
        if self.data.__class__.__name__ == 'GeoDataFrame':
            if self.data.crs is None:
                # Assume EPSG:4326
                self.data.crs = fiona.crs.from_epsg(4326)
                self.epsg = 4326
                return self.epsg
            else:
                crs = self.data.crs.get('init', None)
                if crs and ':' in crs:
                    crs = crs.split(':')[1]
                if crs.isdigit():
                    self.epsg = crs
                    return self.epsg
                else:
                    # Assume EPSG:4326
                    self.epsg = 4326
                    self.data.crs = fiona.crs.from_epsg(4326)
                    return self.epsg
        elif self.data.__class__.__name__ == 'Dataset':
            projection = self.data.GetProjection()
            data_crs = osr.SpatialReference(wkt=projection)
            try:
                self.epsg = data_crs.GetAttrValue('AUTHORITY', 1)
                return self.epsg
            except KeyError:
                # Return the WKT projection instead
                self.epsg = projection
                return projection

    def delete(self):
        """
        Abstract class for deleting the IO source
        :return:
        """
        raise NotImplementedError()


class FeatureIO(GaiaIO):
    """
    GeoJSON Feature Collection IO
    """
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
                # Assume EPSG:4326
                self.data.crs = {'init': 'epsg:4326', 'no_defs': True}
                if 'crs' in features:
                    if 'init' in features['crs']['properties']:
                        self.data.crs = features['crs']['properties']

            else:
                self.data = geopandas.GeoDataFrame.from_features(features)
                # Assume EPSG:4326
                self.data.crs = {'init': 'epsg:4326'}
                if 'crs' in features[0]:
                    if 'init' in features[0]['crs']['properties']:
                        self.data.crs = features[0]['crs']['properties']

        out_data = self.data
        if epsg and self.get_epsg() != epsg:
            out_data = geopandas.GeoDataFrame.copy(out_data)
            out_data[out_data.geometry.name] = \
                self.data.geometry.to_crs(epsg=epsg)
            out_data.crs = fiona.crs.from_epsg(epsg)

        if format == formats.JSON:
            return out_data.to_json()
        else:
            return out_data

    def delete(self):
        """
        Reset the IO data to None
        :return:
        """
        self.data = None


class FileIO(GaiaIO):
    """Abstract class to read and write file data."""

    def __init__(self, uri='', **kwargs):
        """
        :param uri: Filepath of IO object
        :param kwargs:
        :return:
        """
        if uri and self.allowed_folder(uri):
            raise GaiaException(
                "Access to this directory is not permitted : {}".format(
                    os.path.dirname(uri)))
        self.uri = uri
        super(FileIO, self).__init__(uri=uri, **kwargs)
        if self.uri:
            self.ext = os.path.splitext(self.uri)[1].lower()

    def allowed_folder(self, folder):
        """
        Return true or false if folder is in list of
        allowed folders from config
        :param folder: folder to check
        :return: True or False
        """
        allowed_dirs = config['gaia']['fileio_paths'].split(',')
        if not allowed_dirs:
            return True
        filepath = os.path.abspath(os.path.dirname(folder))
        allowed = False
        for path in allowed_dirs:
            if filepath.startswith(path):
                allowed = True
                break
        return allowed

    def delete(self):
        """
        Remove file of IO object
        :return:
        """
        if os.path.exists(self.uri):
            shutil.rmtree(os.path.dirname(self.uri))


class VectorFileIO(FileIO):
    """Read and write vector file data (such as GeoJSON)"""

    default_output = formats.PANDAS

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
        out_data = self.data
        if epsg and self.get_epsg() != epsg:
            out_data = geopandas.GeoDataFrame.copy(out_data)
            out_data[out_data.geometry.name] = \
                self.data.geometry.to_crs(epsg=epsg)
            out_data.crs = fiona.crs.from_epsg(epsg)
        if format == formats.JSON:
            return out_data.to_json()
        else:
            return out_data

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
                outfile.write(self.data.to_json())
        elif as_type == 'shapefile':
            self.data.to_file(filename)
        else:
            raise NotImplementedError('{} not a valid type'.format(as_type))
        return self.uri

    def filter_data(self):
        """
        Apply filters to the dataset
        :return:
        """
        self.data = filter_pandas(self.data, self.filters)


class RasterFileIO(FileIO):
    """Read and write raster data (GeoTIFF)"""

    default_output = formats.RASTER

    def read(self, epsg=None):
        """
        Read data from a raster dataset
        :param epsg: EPSG code to reproject data to
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
        return out_data


class ProcessIO(GaiaIO):
    """IO for nested GaiaProcess objects"""
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
        :return:
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


class GirderIO(GaiaIO):
    """Read and write Girder files/items/metadata"""

    default_output = None

    def __init__(self, name, girder_uris=[], auth=None, **kwargs):
        super(GirderIO, self).__init__(**kwargs)
        raise NotImplementedError


class PostgisIO(GaiaIO):
    """Read PostGIS data"""
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
        :param kwargs:
        :return:
        """
        super(PostgisIO, self).__init__(**kwargs)
        self.table = table
        self.host = kwargs.get('host') or config['gaia']['pg_host']
        self.dbname = kwargs.get('dbname') or config['gaia']['pg_dbname']
        self.user = kwargs.get('user') or config['gaia']['pg_user']
        self.password = kwargs.get('password') or config['gaia']['pg_password']
        self.engine = create_engine(self.get_connection_string())
        self.get_table_info()
        self.verify()

    def verify(self):
        """
        Make sure that all PostgisIO columns exist in the actual table
        :return:
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
        Return the EPSG code of the data
        :return:
        """
        return self.epsg

    def get_table_info(self):
        """
        Use SQLALchemy reflection to gather data on the table, including the
        geometry column, geometry type, and EPSG code
        :return:
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
        Return the geometry type of the data
        :return:
        """
        return self.geometry_type

    def get_query(self):
        """
        Formulate a query string and parameter list based on the
        table name, columns, and filter
        :return:
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
        out_data = self.data
        if epsg and self.get_epsg() != epsg:
            out_data = geopandas.GeoDataFrame.copy(self.data)
            out_data[out_data.geometry.name] = \
                self.data.geometry.to_crs(epsg=epsg)
            out_data.crs = fiona.crs.from_epsg(epsg)
        if format == formats.JSON:
            return out_data.to_json()
        else:
            return out_data


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
