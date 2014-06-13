import ocgis
from ocgis.api.collection import SpatialCollection
from ocgis.conv.fiona_ import GeoJsonConverter

import tempfile
import shutil
import os.path

class convert(object):
	## we can either subset the data by a geometry from a shapefile, or convert to
	## geojson for the entire spatial domain. there are other options here (i.e. a
	## bounding box for tiling or a Shapely geometry).
	def __init__(self, data_var, uri, out):
		self._uri = uri
		self._out = out

		## the target self._variable in the dataset to convert
		self._variable = data_var

	def run(self, output_format='shp', geom_filter=None, time_range=None):
		if (os.path.isabs(os.path.realpath(self._out)) == False):
			## write data to a new temporary directory for each script start
			dir_output = tempfile.mkdtemp()
		else:
			dir_output = os.path.dirname(self._uri)

		prefix = self._out

		## limit the headers in the output.
		out_headers = ['time','year','month','day','value']

		## connect to the dataset and load the data as a field object. this will be used
		## to iterate over time coordinates during the conversion step.
		rd = ocgis.RequestDataset(uri=self._uri, variable=self._variable)
		field = rd.get()

		## selecting specific geometries from a shapefile requires knowing the target
		## geometry's UGID inside the shapefile. shapefile are required to have this
		## identifier at this time as a full attribute search is not enabled. this code
		## searches for TX to find the UGID associated with that state.
		if geom_filter is None:
			select_ugid = None
		else:
			## this argument must always come in as a list
			select_ugid = [select_geom[0]['properties']['UGID']]

		if time_range is None:
			centroid = field.temporal.value_datetime[0]
			time_range = [centroid, centroid]

		## this again is the target dataset with a time range for subsetting now
		rd = ocgis.RequestDataset(uri=self._uri, variable=self._variable,
					  time_range=time_range)

		## parameterize the operations to be performed on the target dataset
		ops = ocgis.OcgOperations(dataset=rd, select_ugid=select_ugid,
								  output_format=output_format, prefix=prefix,
								  dir_output=dir_output,
								  headers=out_headers)
		ret = ops.execute()
		print('path to output file: {0}'.format(ret))
