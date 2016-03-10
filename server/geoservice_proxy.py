#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import re
import requests
import cherrypy
from girder.utility import config


class GeoserviceProxy(object):
    """
    Proxy for an OGC (GeoServer/MapServer) instance.
    Handles GET, POST, and PUT requests.
    The base url, admin username and password must be
    set in the gaia configuration file's 'gaia_ogc' section.
    """

    exposed = True
    config = config.getConfig()
    exposed_services = ('wms', 'wfs', 'wcs', 'wps', 'rest')

    def GET(self, *path, **params):
        return self.parse_request('get', *path, **params)

    def POST(self, *path, **params):
        return self.parse_request('post', *path, **params)

    def PUT(self, *path, **params):
        return self.parse_request('put', *path, **params)

    def parse_request(self, method, *path, **params):
        """
        Send a request to the OGC server and return its response.
        :param method: requests method name (get, post, pull)
        :param path: elements of OGC server URL path
        :param params: request parameters
        :return: OGC server response
        """
        body = None
        headers = {}
        url_parts = list(path)
        service = url_parts[0]
        if service.lower() not in self.exposed_services:
            raise Exception('OGC service {} not allowed'.format(service))
        try:
            headers = cherrypy.request.headers
            if cherrypy.request.body.fp:
                if re.search('xml|text|json|javascript|plain',
                             headers.get('Content-Type') or 'text'):
                    body = cherrypy.request.body.fp.read().decode('utf8')
                else:
                    body = cherrypy.request.body.fp.read()
        except ValueError as ve:
            print(str(ve))
        ogc_url = self.config['gaia_ogc']['ogc_url']
        url_parts.insert(0, ogc_url)
        url = '/'.join(s.strip('/') for s in url_parts)
        func = getattr(requests, method)
        r = func(url, params=params, data=body, headers=headers)
        cherrypy.response.headers['Content-Type'] = \
            r.headers.get('content-type') or None
        return r.content
