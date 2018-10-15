"""
Display options using jupyterlab_geojs
"""

#from gaia.girder_data import GirderDataObject


# Is jupyterlab_geojs available?
try:
    import geojson
    from IPython.display import display
    import jupyterlab_geojs
    IS_GEOJS_LOADED = True
except ImportError as err:
    IS_GEOJS_LOADED = False


def is_loaded():
    """Returns boolean indicating if jupyterlab_geojs is loaded

    :return boolean
    """
    return IS_GEOJS_LOADED


def show(data_objects, **options):
    """Returns geojs scene for JupyterLab display

    :param data_objects: list of GeoData objects to display, in
        front-to-back rendering order.
    :param options: options passed to jupyterlab_geojs.Scene instance.
    :return: jupyterlab_geojs.Scene instance if running Jupyter;
        otherwise returns data_objects for default display
    """
    if not data_objects:
        return None

    if not is_loaded():
        return data_objects

    # (else)
    if not hasattr(data_objects, '__iter__'):
        data_objects = [data_objects]

    #print(data_objects)
    scene = jupyterlab_geojs.Scene(**options)
    scene.create_layer('osm')
    # feature_layer = scene.create_layer('feature')
    feature_layer = None

    combined_bounds = None
    # Reverse order so that first item ends on top
    for data_object in reversed(data_objects):
        # Create map feature
        #print(data_object._getdatatype(), data_object._getdataformat())
        # type is vector, format is [.json, .geojson, .shp, pandas]
        """
        data = data_object.get_data()

        # Can only seem to get json *string*; so parse into json *object*
        json_string = data.to_json()
        json_object = json.loads(json_string)
        feature = feature_layer.create_feature('geojson', json_object)
        #print(json_object)
        feature.enableToolTip = True  # dont work

        geometry = data['geometry']
        bounds = geometry.total_bounds
        """
        meta = data_object.get_metadata()
        #print(meta)
        meta_bounds = meta.get('bounds').get('coordinates')[0]
        #print(meta_bounds)
        assert meta_bounds, 'data_object missing bounds'

        # Bounds format is [xmin, ymin, xmax, ymax]
        bounds = [
            meta_bounds[0][0], meta_bounds[0][1],
            meta_bounds[2][0], meta_bounds[2][1]
        ]

        #print(bounds)
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
                feature_layer = scene.create_layer('feature')

            feature = feature_layer.create_feature(
                'geojson', geojson_collection, **options)
        #elif isinstance(data_object, GirderDataObject) and \
        elif data_object.__class__.__name__ == 'GirderDataObject' and \
            data_object._getdatatype() == 'raster':
            # Use large-image display - only admin can tell if it is installed
            #print(data_object._getdatatype(), data_object._getdataformat())
            tile_url = data_object._get_tile_url()
            print('tile_url', tile_url)
            tile_layer = scene.create_layer('tile', url=tile_url)

    #print(combined_bounds)
    corners = [
        [combined_bounds[0], combined_bounds[1]],
        [combined_bounds[2], combined_bounds[1]],
        [combined_bounds[2], combined_bounds[3]],
        [combined_bounds[0], combined_bounds[3]]
    ]
    scene.set_zoom_and_center(corners=corners)
    #display(scene)
    return scene


def _is_jupyter():
    """Determines if Jupyter is loaded

    return: boolean
    """
    try:
        ipy = get_ipython()
    except NameError as err:
        return False

    # If jupyter, ipy is zmq shell
    return is_instance(ipy, ipkernel.zmqshell.ZMQInteractiveShell)
