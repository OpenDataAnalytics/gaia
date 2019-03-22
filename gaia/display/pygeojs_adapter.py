"""
Display options using pygeojs widget for Jupyter notebooks
"""

# Is jupyterlab_geojs available?
try:
    import geojson
    from IPython.display import display
    import pygeojs
    IS_PYGEOJS_LOADED = True
except ImportError:
    IS_PYGEOJS_LOADED = False

import geopandas

import gaia.types
from gaia.util import GaiaException


def is_loaded():
    """Returns boolean indicating if pygeojs is loaded

    :return boolean
    """
    return IS_PYGEOJS_LOADED


def show(data_objects, **options):
    """Returns pygeojs scene for JupyterLab display

    :param data_objects: list of GeoData objects to display, in
        front-to-back rendering order.
    :param options: options passed to jupyterlab_geojs.Scene instance.
    :return: pygeojs.scene instance if running Jupyter;
        otherwise returns data_objects for default display
    """
    if not is_loaded():
        return data_objects

    # (else)
    if not hasattr(data_objects, '__iter__'):
        data_objects = [data_objects]

    # print(data_objects)
    scene = pygeojs.scene(**options)
    scene.createLayer('osm')

    if not data_objects:
        print('No data objects')
        return scene

    # feature_layer = scene.createLayer('feature')
    feature_layer = None

    combined_bounds = None
    # Reverse order so that first item ends on top
    for data_object in reversed(data_objects):
        if data_object._getdatatype() == gaia.types.VECTOR:
            # print('Adding vector object')
            # Special handling for vector datasets:
            # First, make a copy of the geopandas frame
            df = geopandas.GeoDataFrame.copy(data_object.get_data())

            # Convert to lon-lat if needed
            epsg = data_object.get_epsg()
            if epsg and str(epsg) != '4326':
                print('Converting crs')
                df[df.geometry.name] = df.geometry.to_crs(epsg='4326')

            # Strip any z coordinates (force to z = 1)
            df.geometry = df.geometry.scale(zfact=0.0).translate(zoff=1.0)
            # df.to_file('/home/john/temp/df.pandas')
            # print(df)
            # print(df.geometry)

            # Calculate bounds
            geopandas_bounds = df.geometry.total_bounds
            xmin, ymin, xmax, ymax = geopandas_bounds
            meta_bounds = [
                [xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]
            ]

            # Add map feature
            if feature_layer is None:
                feature_layer = scene.createLayer('feature')

            # Use __geo_interface__ to get the geojson
            feature_layer.readGeoJSON(df.__geo_interface__)
            # print(df.__geo_interface__)
        else:
            # Get bounds, in order to compute overall bounds
            meta = data_object.get_metadata()
            # print('meta: {}'.format(meta))
            # print(meta)
            raster_bounds = meta.get('bounds').get('coordinates')[0]
            # print(meta_bounds)
            assert raster_bounds, 'data_object missing bounds'

            # meta bounds inconsistent between sources, so compute brute force
            xvals, yvals = zip(*raster_bounds)
            xmin, xmax = min(xvals), max(xvals)
            ymin, ymax = min(yvals), max(yvals)
            meta_bounds = [
                [xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]
            ]

        # Bounds format is [xmin, ymin, xmax, ymax]
        bounds = [
            meta_bounds[0][0], meta_bounds[0][1],
            meta_bounds[2][0], meta_bounds[2][1]
        ]

        # print(bounds)
        if combined_bounds is None:
            combined_bounds = bounds
        else:
            combined_bounds[0] = min(combined_bounds[0], bounds[0])
            combined_bounds[1] = min(combined_bounds[1], bounds[1])
            combined_bounds[2] = max(combined_bounds[2], bounds[2])
            combined_bounds[3] = max(combined_bounds[3], bounds[3])

        # print('options:', options)
        rep = options.get('representation')
        if rep == 'outline':
            # Create polygon object
            rect = [
                [bounds[0], bounds[1]],
                [bounds[2], bounds[1]],
                [bounds[2], bounds[3]],
                [bounds[0], bounds[3]],
                [bounds[0], bounds[1]],
            ]
            geojs_polygon = geojson.Polygon([rect])
            properties = {
                'fillColor': '#fff',
                'fillOpacity': 0.1,
                'stroke': True,
                'strokeColor': '#333',
                'strokeWidth': 2
            }
            geojson_feature = geojson.Feature(
                geometry=geojs_polygon, properties=properties)
            geojson_collection = geojson.FeatureCollection([geojson_feature])
            # print(geojson_collection)

            if feature_layer is None:
                feature_layer = scene.createLayer('feature')

            feature_layer.createFeature(
                'geojson', geojson_collection, **options)

        elif data_object.__class__.__name__ == 'GirderDataObject':
            if data_object._getdatatype() == 'raster':
                # Use large-image display
                # Todo - verify that it is installed
                tiles_url = data_object._get_tiles_url()
                # print('tiles_url', tiles_url)
                opacity = 1.0
                if hasattr(data_object, 'opacity'):
                    opacity = data_object.opacity
                scene.createLayer(
                    'osm', url=tiles_url, keepLower=False, opacity=opacity)
            else:
                raise GaiaException(
                    'Cannot display GirderDataObject with data type {}'.format(
                        data_object._getdatatype()))

        elif data_object._getdatatype() == gaia.types.VECTOR:
            pass  # vector objects handled above
        else:
            msg = 'Cannot display dataobject, type {}'.format(
                data_object.__class__.__name__)
            raise GaiaException(msg)

    # Send custom message to (javascript) client to set zoom & center
    rpc = {'method': 'set_zoom_and_center', 'params': combined_bounds}
    scene.send(rpc)
    return scene


def _is_jupyter():
    """Determines if Jupyter is loaded

    return: boolean
    """
    try:
        ipy = get_ipython()
    except NameError:
        return False

    # If jupyter, ipy is zmq shell
    return ipy.__class__.__name__ == 'ZMQInteractiveShell'
