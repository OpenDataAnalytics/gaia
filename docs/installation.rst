Installation
============

These installation instructions are aimed at developers and will install Girder and Gaia from source.

The top level directory of Girder cloned by git will be GIRDER_DIR.

Install of system dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ubuntu 14.04
^^^^^^^^^^^^

Update apt package indices before you start.

::

    sudo apt-get update


- Install Gaia system dependencies

::

    sudo apt-get python-dev libgdal-dev


Install of Gaia and requirements via pip
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # The following 2 lines may or may not be necessary depending on your system:
    export CPLUS_INCLUDE_PATH=/usr/include/gdal
    export C_INCLUDE_PATH=/usr/include/gdal

    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    pip install -e .



Install of Gaia as a Girder plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Install Gaia into the Girder plugins dir from source.

::

    cd GIRDER_DIR/plugins
    git clone https://github.com/OpenGeoScience/gaia.git

-  Install the Python dependencies of Girder plugins, including dev dependencies.

::

    cd GIRDER_DIR
    export IGNORE_PLUGINS=celery_jobs,geospatial,google_analytics,hdfs_assetstore,jquery_widgets,metadata_extractor,mongo_search,oauth,provenance,thumbnails,user_quota,vega,minerva;
    scripts/InstallPythonRequirements.py --mode=dev --ignore-plugins=${IGNORE_PLUGINS}


::

    cd GIRDER_DIR
    npm install

-  copy the ``gaia.dist.cfg`` file, located in the GIRDER_DIR/plugins/gaia/server/conf
   directory, to ``gaia.local.cfg`` in that same directory. Any
   property in ``gaia.local.cfg`` will take precedent over any
   property with the same name in ``gaia.dist.cfg``. If the
   ``gaia.local.cfg`` file is absent, values will be read from
   ``gaia.dist.cfg``.


-  Run the Girder server

::

    cd GIRDER_DIR
    python -m girder


- Navigate to the Admin console in Girder, when you are logged in as an admin user, then click on the Plugins section.

- Enable the Gaia plugin.  Click the button to restart the server.

