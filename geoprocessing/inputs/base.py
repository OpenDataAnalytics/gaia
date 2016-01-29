import os
import geopandas
import rasterio as rasterio
from geoprocessing.core import GaiaException, GaiaRequestParser, getConfig
from geoprocessing.inputs import datatypes, formats



class MissingParameterError(GaiaException):
    pass

class MissingDataException(GaiaException):
    pass

class UnsupportedFormatException(GaiaException):
    pass


class GaiaInput(object):
    """
    Defines an input to be used for a geospatial process
    """

    def __init__(self, name, **kwargs):
        self.name = name
        # self.rawjson = json_data
        # self.inputs = get_io(json_data, is_vector=is_vector)


class GaiaOutput(object):
    """
    Defines an output for a geospatial process
    """
    def __init__(self, name, json_data, **kwargs):
        self.name = name
        self.data = json_data


class GaiaIO(object):
    """
    Abstract IO class for importing/exporting data from a certain source
    """
    data = None
    default_projection = u'epsg:3857'
    filter = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def read(self, *args, **kwargs):
        raise NotImplementedError()

    def write(self, *args, **kwargs):
        raise NotImplementedError()


class FileIO(GaiaIO):
    """
    Read and write file data.
    """
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

    def write(self, data, filepath, is_bin):
        mode = 'b' if is_bin else 't'
        with open(filepath, 'w{}'.format(mode)) as outfile:
            outfile.write(data)


class VectorFileIO(FileIO):
    """
    Read and write vector file data (such as GeoJSON)
    """

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

    def as_df(self):
        if self.data is None:
            raise GaiaException("No data")
        return self.data

    def as_json(self):
        if self.data is None:
            raise GaiaException("No data")
        return self.data.to_json()

    def write(self, data, filepath):
        with open(filepath, 'w') as outfile:
            outfile.write(self.to_json())

    def filter_data(self):
        print self.filter

    def epsg_code(self):
        return int(self.default_projection.split(':')[1])

    def reproject(self):
        original_crs = self.data.crs.get('init', None)
        if original_crs != self.default_projection:
            self.data = self.data.to_crs(epsg=self.epsg_code())


class RasterFileIO(FileIO):
    """
    Read and write raster data (GeoTIFF)
    """

    default_output = formats.RASTER

    def read(self, standardize=True):
        if self.ext not in formats.RASTER:
            raise UnsupportedFormatException(
                "Only the following raster formats are supported: {}".format(
                    ','.join(formats.RASTER)
                )
            )
        super(RasterFileIO, self).read(standardize=standardize)
        self.data = rasterio.open(self.uri)

        if standardize:
            self.reproject()

    def as_df(self):
        if not self.data:
            raise GaiaException("No data")
        return self.data

    def as_json(self):
        if not self.data:
            raise GaiaException("No data")
        return self.data.to_json()

    def write(self, data, filepath):
        with open(filepath, 'w') as outfile:
            outfile.write(self.to_json())

    def reproject(self):
        return
        original_crs = self.data.crs.get('init', None)
        if original_crs != self.default_projection:
            self.data = self.data.to_crs(self.default_projection)


class ProcessIO(GaiaIO):
    """
    IO for nested GaiaProcess objects
    """
    def __init__(self, process, **kwargs):
        super(ProcessIO, self).__init__(**kwargs)
        self.process = process

    def read(self, standardize=True):
        self.process.calculate()
        return self.process.output


class GirderIO(GaiaIO):
    """
    Read and write Girder files/items/metadata
    """
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
    else:
        raise NotImplementedError()