import json
from girder.api.rest import Resource, setRawResponse
from girder.api import access
from girder.api.describe import Description
from girder.utility import config
import xml.etree.ElementTree as et
import requests
import cherrypy


class SimpleWPS(Resource):
    """
    Simplifies WPS requests by accepting a minimal JSON object of parameters
    and from that creates the necessary XML to send to a WPS server, sends the
    request to the WPS server; and passes on the WPS response.

    If the JSON object is empty, the response will be a JSON object
    demonstrating the expected format/content of the request body.

    A default WPS server url and authentication string is provided in the
    gaia configuration file.
    """

    def __init__(self):
        self.resourceName = 'simplewps'
        self.config = config.getConfig()
        self.route('GET', (), self.getCapabilities)
        self.route('POST', (':process',), self.processTask)

    @access.public
    def getCapabilities(self, params):
        """
        Make a GetCapabilities request
        """
        url = params.get('url', self.config['gaia']['wps_default_url'])
        auth = params.get('auth', self.config['gaia']['wps_default_auth'])
        params = {'request': 'GetCapabilities'}
        content, ctype = proxy(url, credentials=auth,
                                method='GET', params=params)
        cherrypy.response.headers['Content-Type'] = ctype
        setRawResponse(True)
        return content
    getCapabilities.description = (
        Description('Fetch the GetCapabilities doc of a WPS service.')
        .param('url', 'The url of the wps source', required=False)
        .param('auth', 'BasicAuth string', required=False)
        .param('version', 'WPS version number', required=False)
        .errorResponse('Read permission denied on the Item.', 403))

    @access.public
    def processTask(self, process, params):
        """
        Based on the process name in the URL and JSON in the request body,
        create & send a WPS request and pass on the response.
        """
        json_body = self.getBodyJson()
        url = json_body.get('url', self.config['gaia']['wps_default_url'])
        auth = json_body.get('auth', self.config['gaia']['wps_default_auth'])
        return_xml = params.get('return_xml')
        wpsProcessClass = globals()[process]
        wpsProcess = wpsProcessClass(json_body)
        if not json_body:
            return wpsProcess.json_help
        else:
            xml_body = wpsProcess.generateXml()
            #Is the XML valid?
            wps_xml = et.fromstring(xml_body)
            xml_body = et.tostring(wps_xml, encoding='utf8', method='xml')
            if return_xml and return_xml.lower() == 'true':
                setRawResponse(True)
                return xml_body
            content, ctype = proxy(url, credentials=auth,
                                   method='POST', body=xml_body)
            if ctype =='application/json':
                return json.loads(content)
            else:
                cherrypy.response.headers['Content-Type'] = ctype
                setRawResponse(True)
                return content
    processTask.description = (
        Description('Make a WPS request and return the response')
        .param('process', 'The process to run', paramType='path')
        .param('body', 'A JSON object containing the wps parameters to add.',
               paramType='body')
        .errorResponse('An error occurred making the WPS request', 500))


class WPSProcess(object):
    """
    Abstract class representing the XML body of a WPS request
    """
    output_format = 'application/json'
    output_result = 'result'

    xml_container="""<?xml version="1.0" encoding="UTF-8"?>
        <wps:Execute version="1.0.0" service="WPS"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns="http://www.opengis.net/wps/1.0.0"
        xmlns:wfs="http://www.opengis.net/wfs"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1"
        xmlns:gml="http://www.opengis.net/gml"
        xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:wcs="http://www.opengis.net/wcs/1.1.1"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xsi:schemaLocation="http://www.opengis.net/wps/1.0.0
        http://schemas.opengis.net/wps/1.0.0/wpsAll.xsd">
          <ows:Identifier>{execute_process}</ows:Identifier>
          <wps:DataInputs>
            {data_inputs}
          </wps:DataInputs>
          <wps:ResponseForm>
            {output_form}
          </wps:ResponseForm>
        </wps:Execute>"""

    raster_layer_xml="""
        <wps:Input>
          <ows:Identifier>{identifier}</ows:Identifier>
          <wps:Reference mimeType="image/tiff"
          xlink:href="http://geoserver/wcs" method="POST">
            <wps:Body>
              <wcs:GetCoverage service="WCS" version="1.1.1">
                <ows:Identifier>{raster}</ows:Identifier>
                <wcs:DomainSubset>
                  <gml:BoundingBox
                    crs="http://www.opengis.net/gml/srs/epsg.xml#4326">
                    <ows:LowerCorner>-180.0 -90.0</ows:LowerCorner>
                    <ows:UpperCorner>180.0 90.0</ows:UpperCorner>
                  </gml:BoundingBox>
                </wcs:DomainSubset>
                <wcs:Output format="image/tiff"/>
              </wcs:GetCoverage>
            </wps:Body>
          </wps:Reference>
        </wps:Input>"""

    vector_layer_xml="""
        <wps:Input>
          <ows:Identifier>{identifier}</ows:Identifier>
          {reference}
        </wps:Input>
    """

    vector_data_reference="""
      <wps:Data>
        <wps:ComplexData mimeType="application/json"><![CDATA[{vector}]]></wps:ComplexData>
      </wps:Data>
    """

    vector_layer_reference="""
      <wps:Reference mimeType="text/xml"
      xlink:href="http://geoserver/wfs" method="POST">
        <wps:Body>
          <wfs:GetFeature service="WFS" version="1.0.0"
          outputFormat="GML2" xmlns:geonode="http://www.geonode.org/">
            <wfs:Query typeName="{vector}"/>
          </wfs:GetFeature>
        </wps:Body>
      </wps:Reference>"""

    attribute_xml = """
        <wps:Input>
          <ows:Identifier>attribute</ows:Identifier>
          <wps:Data>
            <wps:LiteralData>{attribute_field}</wps:LiteralData>
          </wps:Data>
        </wps:Input>"""

    complex_filter_xml = """
        <wps:Input>
          <ows:Identifier>filter</ows:Identifier>
          <wps:Data>
            <wps:ComplexData mimeType="text/plain; subtype=cql">
                <![CDATA[{filter}]]>
            </wps:ComplexData>
          </wps:Data>
        </wps:Input>"""

    output_format_xml="""
        <wps:RawDataOutput mimeType="{output_format}">
          <ows:Identifier>{result}</ows:Identifier>
        </wps:RawDataOutput>"""

    process_name = 'NotImplemented'
    output_format = 'application/json'
    output_result = 'result'
    xml_reference = """
        <wps:Reference mimeType="text/xml; subtype=wfs-collection/1.0"
        xlink:href="http://geoserver/wps"  method="POST">
            <wps:Body>
                <wps:Execute version="1.0.0" service="WPS">
                    <ows:Identifier>{execute_process}</ows:Identifier>
                    <wps:DataInputs>
                        {data_inputs}
                    </wps:DataInputs>
                    <wps:ResponseForm>
                        {output_form}
                    </wps:ResponseForm>
                </wps:Execute>
            </wps:Body>
        </wps:Reference>"""

    def __init__(self, request_json, by_reference=False):
        """
        Create attributes for the class based on JSON input
        :param request_json: the JSON body of the request
        :param by_reference: True if the process is not the outermost
        process to run in a chained request.  False by default.
        :return:
        """
        self.json = request_json
        for key, value in request_json.items():
            setattr(self, key, value)
        if by_reference:
            self.xml_container = self.xml_reference

    def generateInputs(self, **kwargs):
        """
        Create & append the various required inputs for the request
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def generateOutputFormat(self, **kwargs):
        """
        Create/return the 'RawDataOutput' element of a WPS request
        :param kwargs:
        :return:
        """
        return self.output_format_xml.format(
            output_format=self.output_format,
            result=self.output_result)

    def generateRasterInput(self, **kwargs):
        """
        Create/return the InputData element for raster data of a WPS request
        :param kwargs:
        :return:
        """
        return self.raster_layer_xml.format(
            raster=kwargs['layer'],
            identifier=kwargs.get('identifier') or 'data')

    def generateVectorInput(self, **kwargs):
        """
        Create/return the InputData element for vector data of a WPS request
        :param kwargs:
        :return:
        """
        data = kwargs['layer']
        if isinstance(data, dict):
            reference = self.vector_data_reference
            data = json.dumps(data)
        else:
            reference = self.vector_layer_reference

        vector_input = self.vector_layer_xml.format(
            reference=reference,
            identifier=kwargs.get('identifier') or 'features')
        return vector_input.format(
            vector=data)

    def generateXml(self):
        """
        Create/return the XML body for a WPS request
        :param kwargs:
        :return:
        """
        return self.xml_container.format(
            execute_process=self.process_name,
            data_inputs=self.generateInputs(),
            output_form=self.generateOutputFormat())


class ras_RasterZonalStatistics(WPSProcess):
    """
    Implements a ras:RasterZonalStatistics WPS call
    """
    process_name = 'ras:RasterZonalStatistics'
    output_result = 'statistics'
    json_help = {
        "data": "<raster layer typename>",
        "zones": "<vector layer typename or GeoJSON>"
    }

    def generateInputs(self):
        raster_in = self.generateRasterInput(layer=self.data)
        vector_in = self.generateVectorInput(layer=self.zones,
                                             identifier='zones')
        return raster_in + vector_in

class vec_Clip(WPSProcess):
    """
    Implements a vec:Clip WPS call
    """
    process_name = 'vec:Clip'
    json_help = {
        "features": "<vector layer typename>",
        "clip": {
            "features": "<clip layer typename>",
            "attribute": "<name of layer geometry attribute, default is the_geom>",
            "filter": "<CQL query to filter clip layer by>"
        }
    }

    def generateInputs(self):
        layer_input = self.generateVectorInput(layer=self.features)
        clip_json = self.json['clip']
        sub_process = gs_CollectGeometries(clip_json, by_reference=True)
        clip_input = self.vector_layer_xml.format(
            reference=sub_process.generateXml(),
            identifier='clip')
        return layer_input + clip_input


class gs_CollectGeometries(WPSProcess):
    """
    Implements a gs:CollectGeometries WPS call
    """
    process_name = 'gs:CollectGeometries'
    json_help={
        "features": "<vector layer typename>",
        "attribute": "<name of layer geometry attribute, default is the_geom>",
        "filter": "<CQL query to filter clip layer by>"
    }

    def generateInputs(self):
        vec_query = vec_Query(self.json, by_reference=True)
        input = self.vector_layer_xml.format(
            reference=vec_query.generateXml(),
            identifier='features'
        )
        return input


class vec_Query(WPSProcess):
    """
    Implements a vec:Query WPS call
    """
    process_name = 'vec:Query'
    json_help={
        "features": "<vector layer typename>",
        "attribute": "<name of layer geometry attribute, default is the_geom>",
        "filter": "<CQL query to filter clip layer by>"
    }

    def generateInputs(self):
        feature_input = self.generateVectorInput(layer=self.features)
        attribute_input = self.attribute_xml.format(attribute_field=self.attribute)
        filter_input = self.complex_filter_xml.format(filter=self.filter)
        return feature_input + attribute_input + filter_input


class gs_CropCoverage(WPSProcess):
    """
    Implements a gs:CropCoverage WPS call
    """
    process_name = 'gs:CropCoverage'
    json_help = {
        "coverage": "<raster layer typename>",
        "cropShape": {
            "features": "<crop layer typename>",
            "attribute": "<name of layer geometry attribute, default is the_geom>",
            "filter": "<CQL query to filter clip layer by>"
        }
    }

    def generateInputs(self):
        layer_input = self.generateRasterInput(
            layer=self.coverage, identifier='coverage')
        crop_json = self.json['cropShape']
        sub_process = gs_CollectGeometries(crop_json, by_reference=True)
        clip_input = self.vector_layer_xml.format(
            reference=sub_process.generateXml(),
            identifier='cropShape')
        return layer_input + clip_input


def proxy(url, credentials=None, method='POST', params=None, body=None):
    """
    Function for sending a request to and response from a WPS server
    :param url: The URL of the WPS server
    :param credentials: Basic authentication string for the WPS server
    :param method: GET or POST
    :param params: URL parameters to send if any
    :param body: XML body of a WPS POST request
    :return: WPS server response
    """
    headers = None
    if credentials:
        headers = {'Authorization': credentials}
    if method == 'POST':
        r = requests.post(url, params=params, headers=headers, data=body)
    else:
        r = requests.get(url, params=params, headers=headers)
        print r.url
    return r.content, r.headers['content-type']


def load(info):
    info['apiRoot'].simplewps = SimpleWPS()
