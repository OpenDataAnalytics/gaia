#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2015 Kitware Inc.
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

import json
import os
import setuptools
import shutil

from pkg_resources import parse_requirements
from setuptools.command.install import install

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = []
try:
    with open('requirements.txt') as f:
        install_reqs = parse_requirements(f.read())
except Exception:
    pass
reqs = [str(req) for req in install_reqs]

with open('README.md') as f:
    readme = f.read()

extras_require = None

# perform the install
setuptools.setup(
    name='gaia',
    version='0.0.1',
    description='Geoprocessing API',
    long_description=readme,
    author='Kitware, Inc. and Epidemico Inc.',
    author_email='kitware@kitware.com',
    url='http://gaia.readthedocs.org',
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2'
    ],
    extras_require=extras_require,
    packages=setuptools.find_packages(
        exclude=('tests.*', 'tests', 'server.*', 'server')
    ),
    install_requires=reqs,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'gaia-process = gaia.core.__main__:main'
        ]
    }
)
