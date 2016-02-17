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