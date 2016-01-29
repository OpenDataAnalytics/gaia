import sys
import os
from girder.api.rest import Resource, setRawResponse
from girder.api import access
from girder.api.describe import Description
from girder.utility import config
import cherrypy

"""
 TODO: Figure out the best way of making Gaia core functionality
 independent of Girder while still being able to load it as a plugin.
 For now, this path hack does the trick.
"""
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../../')))
import gaia
from gaia.core import GaiaRequestParser


class GeoProcess(Resource):
    """
    Make various geoprocessing requests on Girder data.
    """

    def __init__(self):
        self.resourceName = 'geoprocess'
        self.config = config.getConfig()
        self.route('POST', (':geoprocess',), self.processTask)

    @access.public
    def processTask(self, geoprocess, params):
        """
        Based on the process name in the URL and JSON in the request body,
        create & send a WPS request and pass on the response.
        """
        json_body = self.getBodyJson()

        process = GaiaRequestParser(geoprocess,
                                    data=json_body,
                                    config=self.config).process

        #assume output is GeoJSON or GeoTIFF
        process.calculate()

        if not isinstance(process.output, dict):
            setRawResponse(True)
            cherrypy.response.headers['Content-Type'] = 'image/tiff'
        return process.output
    processTask.description = (
        Description('Make a geoprocessing request and return the response')
            .param('geoprocess', 'The process to run', paramType='path')
            .param('body', 'A JSON object containing the process parameters',
                   paramType='body')
            .errorResponse('An error occurred making the request', 500))


def load(info):
    info['apiRoot'].geoprocess = GeoProcess()
