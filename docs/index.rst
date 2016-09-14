.. Gaia documentation master file, created by
   sphinx-quickstart on Tue Mar 10 15:29:13 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Gaia's documentation!
================================

Gaia is a geospatial analysis library jointly developed by Kitware_ and Epidemico_.
It can work with vector data (geoJSON, shapefiles, PostGIS databases) and raster data (geotiff images).

Inputs and Outputs
-----------

Gaia provides `IO classes <gaia.geo.html#module-gaia.geo.geo_inputs>`__ for reading/writing data from/to various sources:

    * `VectorFileIO <gaia.geo.html#gaia.geo.geo_inputs.VectorFileIO>`__

      * Shapefiles, geoJSON files

    * `FeatureIO <gaia.geo.html#gaia.geo.geo_inputs.FeatureIO>`__

      * geoJSON features defined on object initialization

    * `PostgisIO <gaia.geo.html#gaia.geo.geo_inputs.PostgisIO>`__

      * Spatial tables in a PostGIS database

    * `RasterFileIO <gaia.geo.html#gaia.geo.geo_inputs.RasterFileIO>`__

      * GeoTIFF images

    * `ProcessIO <gaia.geo.html#gaia.geo.geo_inputs.ProcessIO>`__

      * A Gaia process whose output is used as an input for another process.

IO objects for vector data can be filtered via a 'filters' property, such as:

::

    filters=[('type','=','motorway')]

where filters is a list of 3-element tuples.  The first element of the tuple specifies
the feature property to filter by, the second element specifies the comparison being made
(=, <, >, etc), and the third element indicates the property value to filter by.
In the example above, only features where type=motorway will be used.

Examples of IO class usage can be found `here <gaia_examples.html#Data>`__


Processes
___________

Available analyses possible with the core Gaia library include:
  * `Vector processes <gaia.geo.html#module-gaia.geo.processes_vector>`__

    * `Area <gaia.geo.html#gaia.geo.processes_vector.AreaProcess>`__

      * Calculate the areas (in square meters) of polygons in a vector dataset.

      * `Example <gaia_examples.html#Area-Process>`__

    * `Buffer <gaia.geo.html#gaia.geo.processes_vector.BufferProcess>`__

      * Calculate the buffer, specified in meters, around features in a vector dataset

      * `Example <gaia_examples.html#BufferProcess>`__

    * `Centroid <gaia.geo.html#gaia.geo.processes_vector.CentroidProcess>`__

      * Calculate the centroids of polygon features

      * `Example <gaia_examples.html#Centroid>`__

    * `Length <gaia.geo.html#gaia.geo.processes_vector.LengthProcess>`__

      * Calculate the lengths of lines or polygon boundaries.

      * `Example <gaia_examples.html#Length-Process>`__

    * `Distance  <gaia.geo.html#gaia.geo.processes_vector.DistanceProcess>`__

      * Calculate the distance from each feature in one vector dataset to the nearest feature in a second dataset.

      * `Example <gaia_examples.html#Distance-Process>`__

    * `Intersection <gaia.geo.html#gaia.geo.processes_vector.IntersectsProcess>`__

      * Find any features in one dataset that intersect features in another dataset.

      * `Example <gaia_examples.html#Intersects-Process>`__

    * `Cross <gaia.geo.html#gaia.geo.processes_vector.CrossesProcess>`__

      * Find any features in one dataset that cross features in another dataset.

      * `Example <gaia_examples.html#Crosses>`__

    * `Disjoint <gaia.geo.html#gaia.geo.processes_vector.DisjointProcess>`__

      * Find any features in one dataset that do not intersect features in another dataset.

      * `Example <gaia_examples.html#Disjoint>`__

    * `Near <gaia.geo.html#gaia.geo.processes_vector.NearProcess>`__

      * Find features in one dataset within a specified distance (in meters) of features in a second dataset.

      * `Example <gaia_examples.html#Nearby-Process>`__

    * `Within <gaia.geo.html#gaia.geo.processes_vector.WithinProcess>`__

      * Find features in one dataset located inside the features of a second dataset.

      * `Example <gaia_examples.html#Within-Process>`__

    * `Touch <gaia.geo.html#gaia.geo.processes_vector.TouchesProcess>`__

      * Find features in one dataset that touch but do not overlap the features of a second dataset.

      * `Example <gaia_examples.html#Touches>`__

    * `Equals <gaia.geo.html#gaia.geo.processes_vector.EqualsProcess>`__

      * Find features in one dataset that are the same as features in a second dataset.

      * `Example <gaia_examples.html#Equals>`__

    * `Zonal statistics <gaia.geo.html#gaia.geo.processes_vector.ZonalStatsProcess>`__

      * Calculate statistical measures (minimum, maximum, mean, etc) of raster pixel values within each polygon of a vector dataset, and append those measures to the polygons.

      *  `Example <gaia_examples.html#Zonal-Statistics>`__


  * `Raster processes <gaia.geo.html#module-gaia.geo.processes_raster>`__

    * `Subset <gaia.geo.html#gaia.geo.processes_raster.SubsetProcess>`__

      * Given a raster image and a vector dataset defining a polygon, create a new raster image containing only the pixels within the polygon(s).

      *   `Example <gaia_examples.html#Subset-Raster>`__

    * `Raster math <gaia.geo.html#gaia.geo.processes_raster.RasterMathProcess>`__

      * Apply a mathematical equation on 1 or more raster datasets.

      *   `Example <gaia_examples.html#Raster-Math>`__


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

