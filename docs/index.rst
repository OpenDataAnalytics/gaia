.. Gaia documentation master file, created by
   sphinx-quickstart on Tue Mar 10 15:29:13 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Gaia's documentation!
================================

Gaia is a geospatial analysis library jointly developed by Kitware_ and Epidemico_.
It can work with vector data (geoJSON, shapefiles, PostGIS databases) and raster data (geotiff images).

Available analyses possible with the core Gaia library include:
  * `Vector processes <gaia.geo.html#module-gaia.geo.processes_vector>`__

    * Calculate areas of polygons

    * Buffer geometries

    * Calculate centroids

    * Nearest distance

    * Intersections

    * and more.

  * `Raster processes <gaia.geo.html#module-gaia.geo.processes_raster>`__

    * Subset

    * Raster math


There are also official plugins that expand Gaia's capabilities, and you are
encouraged to `write your own <plugins.html#development>`__.


Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   installation
   usage
   plugins
   gaia

.. _Girder: http://www.github.com/Girder/girder
.. _Kitware: http://www.kitware.com
.. _Epidemico: http://epidemico.com
