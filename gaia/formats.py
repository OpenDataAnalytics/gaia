#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc. and Epidemico Inc.
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
import itertools

JSON = ['.json', '.geojson']
SHP = ['.shp']
PANDAS = ['pandas']
VECTOR = list(itertools.chain.from_iterable([JSON, SHP, PANDAS]))
RASTER = ['.tif', '.tiff', '.geotif', '.geotiff']
ALL = VECTOR + RASTER
TEXT = list(itertools.chain.from_iterable([JSON]))
BINARY = list(itertools.chain.from_iterable([RASTER, SHP]))
WEIGHT = ['.gal', '.gwt']
