"""Main builder script for Gaia."""

from setuptools import setup, find_packages

from gaia import __version__

setup(
    name='gaia',
    version=__version__,
    description='A flexible geospatial workflow framework.',

    # long_description from description.rst

    author='Gaia developers',
    author_email='kitware@kitware.com',
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Scientific/Engineering'
    ],
    keywords='geospatial GIS workflow data',
    packages=find_packages(exclude=['tests*', 'docs']),
    require_python='>=2.6',
    url='https://github.com/OpenGeoscience/gaia',
    install_requires=['six', 'requests', 'tabulate']
)
