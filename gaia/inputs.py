import os
import geopandas
import uuid
import gdal
import shutil
import osr
import datatypes
import formats
from gaia.core import GaiaException, config
from gaia.gdal_functions import gdal_reproject


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
    filter = None
    id = None

    def __init__(self, name, **kwargs):
        self.name = name
        self.tmp_dir = config['gaia']['tmp_dir']
        self.default_epsg = config['gaia']['default_epsg']
        self.output_path = config['gaia']['output_path']
        self.process_id = str(uuid.uuid4())
        for k, v in kwargs.items():
            setattr(self, k, v)
        if not self.id:
            self.id = uuid.uuid4()

    def read(self, *args, **kwargs):
        raise NotImplementedError()

    def write(self, *args, **kwargs):
        return ''


class FileIO(GaiaIO):
    """Read and write file data."""
    type = datatypes.FILE

    def __init__(self, name, uri=None, filter=None, **kwargs):
        if self.allowed_folder(uri):
            raise GaiaException(
                "Access to this directory is not permitted : {}".format(
                    os.path.dirname(uri)))
        self.uri = uri
        self.filter = filter
        super(FileIO, self).__init__(name, uri=uri, filter=filter, **kwargs)
        if self.uri:
            self.ext = os.path.splitext(self.uri)[1].lower()

    def allowed_folder(self, folder):
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

    def read(self, standardize=True):
        if not os.path.exists(self.uri):
            raise MissingDataException(
                'Specified file not found: {}'.format(self.uri))

    def write()


class VectorFileIO(FileIO):
    """Read and write vector file data (such as GeoJSON)"""

    default_output = formats.PANDAS

    def read(self, standardize=True):
        if self.ext not in formats.VECTOR:
            raise UnsupportedFormatException(
                "Only the following vector formats are supported: {}".format(
                    ','.join(formats.VECTOR)
                )
            )
        super(VectorFileIO, self).read(standardize=standardize)
        self.data = geopandas.read_file(self.uri)
        if standardize:
            self.reproject()
        if self.filter:
            self.filter_data()

    def as_json(self):
        if self.data is None:
            raise GaiaException("No data")
        return self.data.to_json()

    def write(self, filename, as_type='json'):
        """
        Write data (assumed geopandas) to geojson or shapefile
        :param filename: Base filename
        :param as_type: shapefile or json
        :return: location of file
        """
        output_name = os.path.join(self.output_path, self.id, filename)
        if as_type == 'json':
            with open(output_name, 'w') as outfile:
                outfile.write(self.to_json())
        elif as_type == 'shapefile':
            self.data.to_file(output_name)
        else:
            raise NotImplementedError('{} not a valid type'.format(as_type))
        return output_name

    def filter_data(self):
        print self.filter

    def reproject(self):
        original_crs = self.data.crs.get('init', None)
        if original_crs and ':' in original_crs:
            original_crs = original_crs.split(':')[1]
        if original_crs != self.default_epsg:
            self.data = self.data.to_crs(epsg=self.default_epsg)


class RasterFileIO(FileIO):
    """Read and write raster data (GeoTIFF)"""

    default_output = formats.RASTER

    def read(self, standardize=True):
        if self.ext not in formats.RASTER:
            raise UnsupportedFormatException(
                "Only the following raster formats are supported: {}".format(
                    ','.join(formats.RASTER)
                )
            )
        super(RasterFileIO, self).read(standardize=standardize)
        self.basename = os.path.basename(self.uri)
        self.data = gdal.Open(self.uri)
        if standardize:
            self.reproject()

    def write(self, data, filepath):
        with open(filepath, 'w') as outfile:
            outfile.write(self.to_json())

    def reproject(self):
        data_crs = osr.SpatialReference(wkt=self.data.GetProjection())
        if data_crs.GetAttrValue('AUTHORITY', 1) != self.default_epsg:
            repro_file = os.path.join(self.tmp_dir, self.basename)
            self.data = gdal_reproject(self.uri, repro_file,
                                       epsg=self.default_epsg)
            self.uri = repro_file
            return repro_file


class ProcessIO(GaiaIO):
    """IO for nested GaiaProcess objects"""
    def __init__(self, name, process=None, **kwargs):
        super(ProcessIO, self).__init__(name, **kwargs)
        self.process = process
        self.default_output = process.default_output

    def read(self, standardize=True):
        self.process.compute()
        self.data = self.process.raw_output


class GirderIO(GaiaIO):
    """Read and write Girder files/items/metadata"""

    default_output = None

    def __init__(self, name, girder_uris=[], auth=None, **kwargs):
        super(GirderIO, self).__init__(name, **kwargs)
        raise NotImplementedError


class PostgisIO(GaiaIO):
    """Read and write PostGIS data"""
    default_output = formats.JSON

    def __init__(self, name, connection='', **kwargs):
        super(PostgisIO, self).__init__(name, **kwargs)
        raise NotImplementedError



