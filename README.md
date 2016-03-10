## Gaia

Gaia is a geospatial utilities plugin for [Girder](http://www.github.com/Girder/girder), jointly developed by  [Kitware](http://www.kitware.com) and
[Epidemico](http://epidemico.com).  It provides data processing, transformation, and analysis capabilities specifically targeted for spatial datasets.
Gaia is built on top of popular open source packages such as GDAL and GeoPandas. It will fetch data from multiple sources such as files and databases.

#### Documentation

Documentation for Gaia can be found at http://gaia.readthedocs.org.

#### Installation

System dependencies (Ubuntu):

    sudo apt-get update
    sudo apt-get install python-dev libgdal-dev

System dependencies (OS X):

    brew install gdal --with-postgresql

Gaia install:

    # The following 2 lines may or may not be necessary depending on your system:
    export CPLUS_INCLUDE_PATH=/usr/include/gdal
    export C_INCLUDE_PATH=/usr/include/gdal

    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    pip install -e .

Gaia [![Build Status](https://jenkins.epidemi.co/buildStatus/icon?job=deploy-gaia-development)](https://jenkins.epidemi.co/job/deploy-gaia-development/) [![Coverage Status](https://coveralls.io/repos/OpenGeoscience/gaia/badge.svg)](https://coveralls.io/r/OpenGeoscience/gaia) [![Documentation Status](https://readthedocs.org/projects/gaia/badge/?version=latest)](https://readthedocs.org/projects/gaia/?badge=latest) [![Join the chat at https://gitter.im/OpenGeoscience/gaia](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/OpenGeoscience/gaia?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)


#### License

Copyright 2015 Kitware Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0


Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
