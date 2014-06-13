# Python imports
import os
import sys

# CherryPy imports
import cherrypy

# PyGeo imports
import geoweb
import mongoimp

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir))

def read(expr, vars, time):
    if expr is None:
        return geoweb.empty_result()

    # Check if the data exists in the database. If not then perform
    # a import to extract the metadata
    # @todo Provide means to read this informatio via config
    dbimport = mongoimp.mongo_import("localhost", "documents")

    filename = expr
    if (not (os.path.isfile(filename) and os.path.exists(filename))):
        datadir = cherrypy.request.app.config['/data']['tools.staticdir.dir']
        filename = os.path.join(datadir, filename)

    basename = os.path.basename(filename)
    if not dbimport.is_exists("files", basename):
        dbimport.import_file("files", filename)

    # @todo Implement plugin mechanism to ask each reader if they can
    # read this file for now read using the vtk_reader
    import vtk_reader
    return vtk_reader.read(filename, vars, time)
