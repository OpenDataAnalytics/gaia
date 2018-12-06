from __future__ import print_function
import os
from zipfile import ZipFile

import gaia
from gaia import preprocess

src_folder = os.path.dirname(__file__)
data_folder = os.path.join(src_folder, os.pardir, os.pardir, 'tests', 'data')


## Vector crop
print('VECTOR')

# Load 2 datasets
hospitals = gaia.create(os.path.join(data_folder, 'iraq_hospitals.geojson'))
districts = gaia.create(os.path.join(data_folder, 'baghdad_districts.geojson'))

# Apply crop
print('Before crop (vector)', districts.get_data().shape)
vector_crop = preprocess.crop(hospitals, districts)
print('After crop (vector)', vector_crop.get_data().shape)
#print(cropped.get_data().head())

vector_filename = 'cropped.geojson'
gaia.save(vector_crop, vector_filename)
print('Wrote file {}'.format(vector_filename))

# Readback file and print some info
readback = gaia.create(vector_filename)
print('After readback (vector)', readback.get_data().shape)
#print(readback.get_data().head())


## Raster Crop
print()
print('RASTER')

# Load geometry file
zipfile = ZipFile(os.path.join(data_folder, '2states.zip'), 'r')
zipfile.extract('2states.geojson', data_folder)

try:
    # Load raster file
    airtemp_raster = gaia.create(os.path.join(data_folder, 'globalairtemp.tif'))
    print('type: {}'.format(type(airtemp_raster)))
    print('meta: {}'.format(airtemp_raster.get_metadata()))
    two_states = gaia.create(os.path.join(data_folder, '2states.geojson'))
    raster_crop = preprocess.crop(airtemp_raster, two_states)
    epsg = raster_crop.get_epsg()
    print('epsg: {}'.format(epsg))

    raster_filename = 'cropped.tif'
    gaia.save(raster_crop, raster_filename)
finally:
    testfile = os.path.join(data_folder, '2states.geojson')
    if os.path.exists(testfile):
        os.remove(testfile)
