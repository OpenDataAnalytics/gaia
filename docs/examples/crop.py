from __future__ import print_function
import os
import gaia
from gaia import preprocess

src_folder = os.path.dirname(__file__)
data_folder = os.path.join(src_folder, os.pardir, os.pardir, 'tests', 'data')

# Load 2 datasets
hospitals = gaia.create(os.path.join(data_folder, 'iraq_hospitals.geojson'))
districts = gaia.create(os.path.join(data_folder, 'baghdad_districts.geojson'))

# Apply crop
print('Before crop', districts.get_data().shape)
cropped = preprocess.crop(hospitals, districts)
print('After crop', cropped.get_data().shape)
#print(cropped.get_data().head())

filename = 'test.geojson'
with open(filename, 'w') as f:
    f.write(cropped.get_data().to_json())

# Readback file and print some info
readback = gaia.create(filename)
print('After readback', readback.get_data().shape)
#print(readback.get_data().head())
