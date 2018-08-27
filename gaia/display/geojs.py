"""
Display options using jupyterlab_geojs
"""


# Is jupyterlab_geojs available?
try:
    import json
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
    feature_layer = scene.create_layer('feature')

    combined_bounds = None
    # Reverse order so that first item ends on top
    for data_object in reversed(data_objects):
        # Create map feature
        #print(data_object._getdatatype(), data_object._getdataformat())
        # type is vector, format is [.json, .geojson, .shp, pandas]
        data = data_object.get_data()

        # Can only seem to get json *string*; so parse into json *object*
        json_string = data.to_json()
        json_object = json.loads(json_string)
        feature = feature_layer.create_feature('geojson', json_object)
        #print(json_object)
        feature.enableToolTip = True  # dont work

        geometry = data['geometry']
        bounds = geometry.total_bounds
        #print(bounds)
        if combined_bounds is None:
            combined_bounds = bounds
        else:
            combined_bounds[0] = min(combined_bounds[0], bounds[0])
            combined_bounds[1] = min(combined_bounds[1], bounds[1])
            combined_bounds[2] = max(combined_bounds[2], bounds[2])
            combined_bounds[3] = max(combined_bounds[3], bounds[3])

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
