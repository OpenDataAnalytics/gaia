import logging
from gaia import formats
from gaia.geo.processes_base import GaiaProcess
from gaia.geo.gdal_functions import gdal_calc, gdal_clip
from gaia.inputs import RasterFileIO

logger = logging.getLogger('gaia.processes_raster')


class SubsetProcess(GaiaProcess):
    """
    Generates a raster dataset representing the portion of the input raster
    dataset that is contained within a vector polygon.
    """
    required_inputs = (('clip', formats.JSON), ('raster', formats.RASTER))
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

    def compute(self):
        super(SubsetProcess, self).compute()
        clip_df = self.inputs[0].read()
        raster_img = self.inputs[1].read()
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
    optional_args = ('bands', 'nodata', 'allBands', 'output_type')
    default_output = formats.RASTER

    def __init__(self, **kwargs):
        super(RasterMathProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = RasterFileIO(name='result',
                                       uri=self.get_outpath())

    def compute(self):
        super(RasterMathProcess, self).compute()

        calculation = self.args['calc']
        rasters = [x.read() for x in self.inputs]
        bands = self.args.get('bands' or None)
        nodata = self.args.get('nodata' or None)
        all_bands = self.args.get('allBands' or None)
        otype = self.args.get('output_type' or None)
        self.output.create_output_dir(self.output.uri)
        self.output.data = gdal_calc(calculation,
                                     self.output.uri,
                                     rasters,
                                     bands=bands,
                                     nodata=nodata,
                                     allBands=all_bands,
                                     output_type=otype)
