from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)
import json
import urllib

from gaia.gaia_data import GaiaDataObject
from gaia.io.girder_interface import GirderInterface


class GirderDataObject(GaiaDataObject):
    """Proxies either a file or a folder on girder

    """
    def __init__(self, reader, resource_type, resource_id, **kwargs):
        super(GirderDataObject, self).__init__(**kwargs)
        """

        Optional bounds input provided because some girder assetstores
        are not configured for geometa
        """
        self._reader = reader
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.mapnik_style = None
        self.bounds = kwargs.get('bounds')
        # print('Created girder object, resource_id: {}'.format(resource_id))

    def get_metadata(self, force=False):
        if force or not self._metadata:
            gc = GirderInterface._get_girder_client()
            metadata = gc.get('item/{}/geometa'.format(self.resource_id))
            # print('returned metadata: {}'.format(metadata))
            self._metadata = metadata

            if self.bounds:
                geom = self._bounds_to_geom(self.bounds)
                self._metadata['bounds'] = geom
        return self._metadata

    def set_mapnik_style(self, style):
        """A convenience method for applying mapnik styles for large-image

        Example style object:
            {
                'band': 1,
                'max': 5000,
                'min': 2000,
                'palette': 'matplotlib.Plasma_6',
                'scheme': 'linear'
            }

        """
        self.mapnik_style = style

    def _get_tiles_url(self):
        """Constructs url for large_image display

        Returns None for non-raster datasets
        """
        if self._getdatatype() != 'raster':
            return None

        # (else)
        girder_url = GirderInterface.get_instance().girder_url
        base_url = '{}/api/v1/item/{}/tiles/zxy/{{z}}/{{x}}/{{y}}'.format(
            girder_url, self.resource_id)
        mapnik_string = ''
        if self.mapnik_style:
            if isinstance(self.mapnik_style, str):
                style_string = self.mapnik_style
            else:
                style_string = json.dumps(self.mapnik_style)
            encoded_string = urllib.parse.quote_plus(style_string)
            mapnik_string = '&style={}'.format(encoded_string)
        tiles_url = '{}?encoding=PNG&projection=EPSG:3857{}'.format(
            base_url, mapnik_string)

        # print('Using tiles_url:', tiles_url)
        return tiles_url

    def _bounds_to_geom(self, bounds):
        """Converts bounds as [xmin,ymin,xmax,ymax] to geojson polygon

        :bounds: list of doubles xmin, ymin, xmax, ymax

        For internal use. Needed for certain assetstores which either don't
        provide bounds or provide incorrect bounds data.
        """
        xmin, ymin, xmax, ymax = bounds
        coords = [[
            [xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]
        ]]
        geom = {
            'coordinates': coords,
            'type': 'Polygon'
        }
        return geom
