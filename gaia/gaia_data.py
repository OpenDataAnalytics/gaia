from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

from sqlalchemy import create_engine, MetaData, Table, text
from geoalchemy2 import Geometry
import fiona
import geopandas
try:
    import osr
except ImportError:
    from osgeo import osr

from gaia.filters import filter_postgis
from gaia.geo.gdal_functions import gdal_reproject
from gaia.util import GaiaException, sqlengines


class GaiaDataObject(object):
    def __init__(self, reader=None, dataFormat=None, epsg=None, **kwargs):
        self._data = None
        self._metadata = None
        self._reader = reader
        self._datatype = None
        self._dataformat = dataFormat
        self._epsg = epsg

    def get_metadata(self):
        if not self._metadata:
            self._reader.load_metadata(self)
        return self._metadata

    def set_metadata(self, metadata):
        self._metadata = metadata

    def get_data(self):
        if self._data is None:
            self._reader.load_data(self)
        return self._data

    def set_data(self, data):
        self._data = data

    def get_epsg(self):
        return self._epsg

    def reproject(self, epsg):
        repro = geopandas.GeoDataFrame.copy(self._data)
        repro[repro.geometry.name] = repro.geometry.to_crs(epsg=epsg)
        repro.crs = fiona.crs.from_epsg(epsg)
        self._data = repro

    def _getdatatype(self):
        if not self._datatype:
            self.get_metadata()
            if not self._datatype:
                self._datatype = self._metadata.get('type_', 'unknown')

        return self._datatype

    def _setdatatype(self, value):
        self._datatype = value

    datatype = property(_getdatatype, _setdatatype)

    def _getdataformat(self):
        if not self._dataformat:
            self.get_metadata()

        return self._dataformat

    def _setdataformat(self, value):
        self._dataformat = value

    dataformat = property(_getdataformat, _setdataformat)


class GDALDataObject(GaiaDataObject):
    def __init__(self, reader=None, **kwargs):
        super(GDALDataObject, self).__init__(**kwargs)
        self._reader = reader
        self._epsgComputed = False

    def get_epsg(self):
        if not self._epsgComputed:
            if not self._data:
                self.get_data()

            projection = self._data.GetProjection()
            data_crs = osr.SpatialReference(wkt=projection)

            try:
                self.epsg = int(data_crs.GetAttrValue('AUTHORITY', 1))
                self._epsgComputed = True
            except KeyError:
                raise GaiaException("EPSG code coud not be determined")

        return self.epsg

    def reproject(self, epsg):
        self._data = gdal_reproject(self._data, '', epsg=epsg)
        self.epsg = epsg


class PostgisDataObject(GaiaDataObject):
    def __init__(self, reader=None, **kwargs):
        super(PostgisDataObject, self).__init__(**kwargs)

        self._reader = reader

        self._table = None
        self._hostname = None
        self._dbname = None
        self._user = None
        self._password = None
        self._columns = []
        self._filters = None
        self._geom_column = 'the_geom'
        self._epsg = None
        self._meta = None
        self._table_obj = None

    # Define table property
    def _settable(self, table):
        self._table = table

    def _gettable(self):
        return self._table

    table = property(_gettable, _settable)

    # Define hostname property
    def _sethostname(self, hostname):
        self._hostname = hostname

    def _gethostname(self):
        return self._hostname

    hostname = property(_gethostname, _sethostname)

    # Define db property
    def _setdbname(self, dbname):
        self._dbname = dbname

    def _getdbname(self):
        return self._dbname

    dbname = property(_getdbname, _setdbname)

    # Define user property
    def _setuser(self, user):
        self._user = user

    def _getuser(self):
        return self._user

    user = property(_getuser, _setuser)

    # Define password property
    def _setpassword(self, password):
        self._password = password

    def _getpassword(self):
        return self._password

    password = property(_getpassword, _setpassword)

    # Define epsg property
    def _setepsg(self, epsg):
        self._epsg = epsg

    def _getepsg(self):
        return self._epsg

    epsg = property(_getepsg, _setepsg)

    # Define filters property
    def _setfilters(self, filters):
        self._filters = filters

    def _getfilters(self):
        return self._filters

    filters = property(_getfilters, _setfilters)

    # Define geom_column property
    def _setgeom_column(self, geom_column):
        self._geom_column = geom_column

    def _getgeom_column(self):
        return self._geom_column

    geom_column = property(_getgeom_column, _setgeom_column)

    # Define engine property
    def _setengine(self, engine):
        self._engine = engine

    def _getengine(self):
        return self._engine

    engine = property(_getengine, _setengine)

    # etc...

    def initialize_engine(self):
        self._engine = self.get_engine(self.get_connection_string())

        self.get_table_info()
        self.verify()

    # methods additional in PostgisIO

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
        for col in self._columns:
            if col not in self._table_obj.columns.keys():
                raise GaiaException('{} column not found in {}'.format(
                    col, self._table_obj))

    def get_connection_string(self):
        """
        Get connection string based on host, dbname, username, password

        :return: Postgres connection string for SQLAlchemy
        """
        auth = ''
        if self._user:
            auth = self._user
        if self._password:
            auth = auth + ':' + self._password
        if auth:
            auth += '@'
        conn_string = 'postgresql://{auth}{host}/{dbname}'.format(
            auth=auth, host=self._hostname, dbname=self._dbname)

        return conn_string

    def get_epsg(self):
        """
        Get the EPSG code of the data

        :return: EPSG code
        """
        return self._epsg

    def get_table_info(self):
        """
        Use SQLALchemy reflection to gather data on the table, including the
        geometry column, geometry type, and EPSG code, and assign to the
        PostgisIO object's attributes.
        """
        epsg = None
        meta = MetaData()
        table_obj = Table(self._table, meta,
                          autoload=True, autoload_with=self._engine)
        if not self._columns:
            self._columns = table_obj.columns.keys()
        geo_cols = [(col.name, col.type) for col in table_obj.columns
                    if hasattr(col.type, 'srid')]
        if geo_cols:
            geo_col = geo_cols[0]
            self._geom_column = geo_col[0]
            geo_obj = geo_col[1]
            if self._geom_column not in self._columns:
                self._columns.append(self._geom_column)
            if hasattr(geo_obj, 'srid'):
                epsg = geo_obj.srid
                if epsg == -1:
                    epsg = 4326
            if hasattr(geo_obj, 'geometry_type'):
                self._geometry_type = geo_obj.geometry_type

        self._epsg = epsg
        self._table_obj = table_obj
        self._meta = meta

    def get_geometry_type(self):
        """
        Get the geometry type of the data

        :return: Geometry type
        """
        return self._geometry_type

    def get_query(self):
        """
        Formulate a query string and parameter list based on the
        table name, columns, and filter

        :return: Query string
        """
        columns = ','.join(['"{}"'.format(x) for x in self._columns])
        query = 'SELECT {} FROM "{}"'.format(columns, self._table)
        filter_params = []
        if self._filters:
            filter_sql, filter_params = filter_postgis(self._filters)
            query += ' WHERE {}'.format(filter_sql)
        query += ';'
        return str(text(query)), filter_params
