"""
Display options using pygeojs widget for Jupyter notebooks
"""

# Is jupyterlab_geojs available?
try:
    import geojson
    from IPython.display import display
    import pygeojs
    IS_PYGEOJS_LOADED = True
except ImportError as err:
    IS_PYGEOJS_LOADED = False


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

    #print(data_objects)
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
                feature_layer = scene.createLayer('feature')

            feature = feature_layer.createFeature(
                'geojson', geojson_collection, **options)
        #elif isinstance(data_object, GirderDataObject) and \
        elif data_object.__class__.__name__ == 'GirderDataObject' and \
            data_object._getdatatype() == 'raster':
            # Use large-image display - only admin can tell if it is installed
            #print(data_object._getdatatype(), data_object._getdataformat())
            tiles_url = data_object._get_tiles_url()
            print('tiles_url', tiles_url)
            opacity = data_object.opacity
            tile_layer = scene.createLayer('osm', url=tiles_url, keepLower=False, opacity=opacity)

    corners = [
        [combined_bounds[0], combined_bounds[1]],
        [combined_bounds[2], combined_bounds[1]],
        [combined_bounds[2], combined_bounds[3]],
        [combined_bounds[0], combined_bounds[3]]
    ]
    # Todo add background comm to call geojs.map.setZoomAndCenter():
    # scene.set_zoom_and_center(corners=corners)
    # For now, we'll have to settle for centering
    scene.center = {
        'x': 0.5 * (combined_bounds[0] + combined_bounds[2]),
        'y': 0.5 * (combined_bounds[3] + combined_bounds[3])
    }
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
    return isinstance(ipy, ipkernel.zmqshell.ZMQInteractiveShell)
