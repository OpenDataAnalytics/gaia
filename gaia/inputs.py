import json
import os
import errno
import geopandas
import gdal
import shutil
try:
    import osr
except ImportError:
    from osgeo import osr
import gaia.formats as formats
from gaia.core import GaiaException, config
from gaia.filters import filter_pandas
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
    default_output = None

    def __init__(self, **kwargs):
        self.tmp_dir = config['gaia']['tmp_dir']
        self.default_epsg = config['gaia']['default_epsg']
        for k, v in kwargs.items():
            setattr(self, k, v)

    def read(self, *args, **kwargs):
        raise NotImplementedError()

    def write(self, *args, **kwargs):
        pass

    def create_output_dir(self, filename):
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise

    def get_epsg(self):
        if self.data is None:
            self.read()
        if self.data.__class__.__name__ == 'GeoDataFrame':
            crs = self.data.crs.get('init', None)
            if crs and ':' in crs:
                crs = crs.split(':')[1]
            if crs.isdigit():
                self.epsg = crs
                return self.epsg
            else:
                # Assume EPSG:4326
                self.epsg = 4326
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
        raise NotImplementedError()


class FeatureIO(GaiaIO):
    """
    GeoJSON Feature Collection IO
    """
    default_output = formats.PANDAS

    def __init__(self,  features=None, **kwargs):
        super(FeatureIO, self).__init__(**kwargs)
        self.features = features

    def read(self):
        if self.data is None and self.features:
            if type(self.features) == str:
                self.features = json.loads(self.features)
            features = self.features

            if 'type' in features and features['type'] == 'FeatureCollection':
                self.data = geopandas.GeoDataFrame.from_features(
                    self.features['features'])
                # Assume EPSG:4326
                self.data.crs = {'init': 'epsg:4326'}
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
        return self.data

    def delete(self):
        self.data = None


class FileIO(GaiaIO):
    """Read and write file data."""

    def __init__(self, uri=None, filter=None, **kwargs):
        if uri and self.allowed_folder(uri):
            raise GaiaException(
                "Access to this directory is not permitted : {}".format(
                    os.path.dirname(uri)))
        self.uri = uri
        self.filter = filter
        super(FileIO, self).__init__(uri=uri, filter=filter, **kwargs)
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

    def read(self, standardize=False):
        if not os.path.exists(self.uri):
            raise MissingDataException(
                'Specified file not found: {}'.format(self.uri))

    def delete(self):
        if os.path.exists(self.uri):
            shutil.rmtree(os.path.dirname(self.uri))


class VectorFileIO(FileIO):
    """Read and write vector file data (such as GeoJSON)"""

    default_output = formats.PANDAS

    def read(self, standardize=False, format=None):
        if not format:
            format = self.default_output
        if self.ext not in formats.VECTOR:
            raise UnsupportedFormatException(
                "Only the following vector formats are supported: {}".format(
                    ','.join(formats.VECTOR)
                )
            )
        super(VectorFileIO, self).read()
        if self.data is None:
            self.data = geopandas.read_file(self.uri)
            if self.filter:
                self.filter_data()
        if format == formats.JSON:
            return self.data.to_json()
        else:
            return self.data

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
        self.data = filter_pandas(self.data, self.filter)


class RasterFileIO(FileIO):
    """Read and write raster data (GeoTIFF)"""

    default_output = formats.RASTER

    def read(self):
        if self.ext not in formats.RASTER:
            raise UnsupportedFormatException(
                "Only the following raster formats are supported: {}".format(
                    ','.join(formats.RASTER)
                )
            )
        super(RasterFileIO, self).read()
        self.basename = os.path.basename(self.uri)
        if not self.data:
            self.data = gdal.Open(self.uri)
        return self.data


class ProcessIO(GaiaIO):
    """IO for nested GaiaProcess objects"""
    def __init__(self, process=None, parent=None, **kwargs):
        super(ProcessIO, self).__init__(**kwargs)
        self.process = process
        self.parent = parent
        self.default_output = process.default_output

    def read(self):
        if self.data is None:
            self.process.compute()
            self.data = self.process.output.data
        return self.data


class GirderIO(GaiaIO):
    """Read and write Girder files/items/metadata"""

    default_output = None

    def __init__(self, name, girder_uris=[], auth=None, **kwargs):
        super(GirderIO, self).__init__(**kwargs)
        raise NotImplementedError


class PostgisIO(GaiaIO):
    """Read and write PostGIS data"""
    default_output = formats.JSON

    def __init__(self, name, connection='', **kwargs):
        super(PostgisIO, self).__init__(**kwargs)
        raise NotImplementedError


def reproject(dataio, epsg):
    dataset = dataio.read()
    dataclass = dataset.__class__.__name__
    original_crs = dataio.get_epsg()
    # Run appropriate reprojection method

    if original_crs != epsg:
        if dataclass == 'GeoDataFrame':
            dataio.data = dataset.to_crs(epsg=epsg)
            dataio.epsg = epsg
        elif dataclass == 'Dataset':
            dataio.data = gdal_reproject(dataset, '', epsg=epsg)
            dataio.epsg = epsg
