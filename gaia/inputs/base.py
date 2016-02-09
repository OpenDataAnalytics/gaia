import os
import geopandas
import uuid
import gdal
import shutil
import osr
from gaia.core import GaiaException, GaiaRequestParser, getConfig
from gaia.inputs import datatypes, formats
from gaia.processes.gdal_functions import gdal_reproject


class MissingParameterError(GaiaException):
    """Raise when a required parameter is missing"""
    pass


class MissingDataException(GaiaException):
    """Raise when required data is missing"""
    pass


class UnsupportedFormatException(GaiaException):
    """Raise when an unsupported data format is used"""
    pass


class GaiaInput(object):
    """Defines an input to be used for a geospatial process"""

    def __init__(self, name, **kwargs):
        self.name = name
        self.io = None
        for k, v in kwargs.items():
            setattr(self, k, v)

    def data(self):
        if self.io:
            return self.io.data
        return None


class GaiaOutput(object):
    """Defines an output for a geospatial process"""
    def __init__(self, name, result, **kwargs):
        self.name = name
        self.data = result
        for k, v in kwargs.items():
            setattr(self, k, v)

class GaiaIO(object):
    """Abstract IO class for importing/exporting data from a certain source"""
    data = None
    filter = None

    def __init__(self, **kwargs):
        config = getConfig()
        self.tmp_dir = config['gaia']['tmp_dir']
        self.default_epsg = config['gaia']['default_epsg']
        self.output_path = config['gaia']['output_path']
        self.id = str(uuid.uuid4())
        for k, v in kwargs.items():
            setattr(self, k, v)

    def read(self, *args, **kwargs):
        raise NotImplementedError()

    def write(self, *args, **kwargs):
        raise NotImplementedError()


class FileIO(GaiaIO):
    """Read and write file data."""
    type = datatypes.FILE

    def __init__(self, uri=None, filter=None, **kwargs):
        if self.allowed_folder(uri):
            raise GaiaException(
                "Access to this directory is not permitted : {}".format(
                    os.path.dirname(uri)))
        self.uri = uri
        self.filter = filter
        super(FileIO, self).__init__(uri=uri, filter=filter)
        self.ext = os.path.splitext(self.uri)[1].lower()

    def allowed_folder(self, folder):
        config = getConfig()
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

    def delete(self):
        output_folder = os.path.join(self.output_path, self.id)
        shutil.rmtree(output_folder)


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
    def __init__(self, process, **kwargs):
        super(ProcessIO, self).__init__(**kwargs)
        self.process = process
        self.default_output = process.default_output

    def read(self, standardize=True):
        self.process.compute()
        self.data = self.process.raw_output


class GirderIO(GaiaIO):
    """Read and write Girder files/items/metadata"""

    default_output = None

    def __init__(self, girder_uris, auth, **kwargs):
        super(ProcessIO, self).__init__(**kwargs)
        raise NotImplementedError


class PostgisIO(GaiaIO):
    """Read and write PostGIS data"""
    default_output = formats.JSON

    def __init__(self, girder_uris, auth, **kwargs):
        super(ProcessIO, self).__init__(**kwargs)
        raise NotImplementedError


def is_vector(filename):
    try:
        return os.path.splitext(filename)[1] in formats.VECTOR
    except IndexError:
        return False


def create_io(data):
    if data['type'] == 'file':
        io = VectorFileIO(**data) if is_vector(
            data['uri']) else RasterFileIO(**data)
        return io
    elif data['type'] == 'process':
        process_name = data['process']['name']
        parser = GaiaRequestParser(process_name, data=data['process'])
        return ProcessIO(parser.process)
    # elif data['type'] == 'girder':
    #     return GirderIO(**data)
    # elif data['type'] == 'wfs':
    #     return WfsIO(**data)
    # elif data['type'] == 'wfs':
    #     return WpsIO(**data)
    # elif data['type'] == 'raw':
    #     return GaiaIO(**data)
    # elif data['type'] == 'pg':
    #     return PostgisIO(**data)
    else:
        raise NotImplementedError()
