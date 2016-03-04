import logging
from gaia import formats
from gaia.geo.gaia_process import GaiaProcess
from gaia.geo.gdal_functions import gdal_calc, gdal_clip
from gaia.inputs import RasterFileIO

logger = logging.getLogger('gaia.geo')


class SubsetProcess(GaiaProcess):
    """
    Generates a raster dataset representing the portion of the input raster
    dataset that is contained within a vector polygon.
    """
    required_inputs = (('raster', formats.RASTER), ('clip', formats.JSON))
    default_output = formats.RASTER

    def __init__(self, **kwargs):
        """
        Create a process to subset a raster by a vector polygon
        :param clip_io: IO object containing vector polygon data
        :param raster_io: IO object containing raster data
        :param kwargs:
        :return: SubsetProcess object
        """
        super(SubsetProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = RasterFileIO(name='result',
                                       uri=self.get_outpath())
        self.validate()

    def compute(self):
        raster, clip = self.inputs[0], self.inputs[1]
        raster_img = raster.read()
        clip_df = clip.read(epsg=raster.get_epsg())
        # Merge all features in vector input
        raster_output = self.output.uri
        self.output.create_output_dir(raster_output)
        clip_json = clip_df.geometry.unary_union.__geo_interface__
        self.output.data = gdal_clip(raster_img, raster_output, clip_json)


class RasterMathProcess(GaiaProcess):
    """
    Performs raster math/algebra based on supplied arguments.
    Inputs should consist of at least one raster IO object.
    Required arg is 'calc', an equation for the input rasters.
    Example: "A + B / (C * 2.4)".  The letters in the equation
    should correspond to the names of the inputs.
    """
    required_inputs = (('A', formats.RASTER),)
    required_args = ('calc',)
    default_output = formats.RASTER

    bands = None
    nodata = None
    all_bands = None
    output_type = None

    def __init__(self, calc=None, **kwargs):
        super(RasterMathProcess, self).__init__(**kwargs)
        self.calc = calc
        if not self.output:
            self.output = RasterFileIO(name='result',
                                       uri=self.get_outpath())
        self.validate()

    def compute(self):
        first = self.inputs[0]
        epsg = first.get_epsg()
        rasters = [x.read(epsg=epsg) for x in self.inputs]
        bands = self.bands
        nodata = self.nodata
        all_bands = self.all_bands
        otype = self.output_type
        self.output.create_output_dir(self.output.uri)
        self.output.data = gdal_calc(self.calc,
                                     self.output.uri,
                                     rasters,
                                     bands=bands,
                                     nodata=nodata,
                                     allBands=all_bands,
                                     output_type=otype)
