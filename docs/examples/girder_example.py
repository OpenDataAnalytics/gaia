import json
import sys

import geojson

import gaia

"""
girder_url='https://data.kitware.com'
apikey = 'WQMfRhZn7ymUo8iMMXTej8MOx4OjXVIf3Hsvk12J'
gaia.connect(girder_url=girder_url, apikey=apikey)

# Maybe a method to generate girder url?
utm_tiff_id = '5b1e99b58d777f2e622561e2'
ny_geojs_id = '5ad8e9678d777f0685794ac9'
sfbay_tiff_id = '5babd80c8d777f06b90730d1'
resource_url = 'girder://file/{}'.format(sfbay_tiff_id)
"""
#girder_url = 'http://localhost:8989'
user = 'admin'
pw = 'letmein'
gaia.connect(username=user, password=pw)

# Create gaia dataset for girder-hosted file
item_id = '5bae2975e44298008d78ac90'  # DEM_bare_earth.tif (4+ GB)
resource_url = 'girder://item/{}'.format(item_id)
dataset = gaia.create(resource_url)
meta = dataset.get_metadata()
print()
# print(json.dumps(meta, sort_keys=True, indent=2))
print('Input dataset width {}, height {}'.format(meta['width'], meta['height']))

# Generate crop geometry (small!)
bounds = meta.get('bounds',{}).get('coordinates')[0]
assert bounds, 'Dataset bounds missing'
# print()
# print(bounds)

# Compute center coordinates
x = (bounds[0][0] + bounds[2][0]) / 2.0
y = (bounds[0][1] + bounds[2][1]) / 2.0

# Use smll percentage of height & width
dx = 0.005 * (bounds[2][0] - bounds[0][0])
dy = 0.005 * (bounds[2][1] - bounds[0][1])
rect = [
    [x,y], [x, y-dy], [x-dx, y-dy], [x-dx, y], [x,y]
]
# print()
# print(rect)

# Must pass rectangle in as a LIST, in order to get geom formatted the way resgeodata uses
crop_geom = geojson.Polygon([rect])
# print()
# print(crop_geom)

# Perform crop operation
from gaia import preprocess
cropped_dataset = preprocess.crop2(dataset, crop_geom, name='crop100m.tif')
print()
cropped_meta = cropped_dataset.get_metadata()
print('Cropped dataset width {}, height {}'.format(
    cropped_meta['width'], cropped_meta['height']))
print(cropped_meta)

print('finis', dataset)
