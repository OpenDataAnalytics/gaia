Plugins
============

Gaia has a plugin system to expand its built-in capabilities.  A Gaia plugin
will typically include new input/output classes and processor classes.

Installation
-----------------
To install a Gaia plugin, git clone it's repository and then install with::

  pip install -e .

or::

  python setup.py install

Depending on the plugin may also need to install additional dependencies::

  pip install -r requirements.txt

A plugin can also include a configuration file (typically 'gaia.cfg') that you may need to modify.



Development
-----------------
An example demo plugin is available at https://github.com/mbertrand/gaia_plugin_demo

To create your own plugins, please follow these guidelines:

- Name your plugin with a prefix of 'gaia-'
- Include a setup.py file that includes an 'entry_points' attribute, in the form::

    entry_points={
          'gaia.plugins': [
             "your_plugin_module = your_plugin_package.your_plugin_module",
             "another_plugin_module = your_plugin_package.another_plugin_module"
          ]
    }

- For each of your plugin modules, include a PLUGIN_CLASS_EXPORTS property that contains the classes you wish to make available to the Gaia parser.  For example::

    PLUGIN_CLASS_EXPORTS = [
        PluginModuleClassOne,
        PluginModuleClassTwo,
    ]

- If your plugin requires additional configuration properties not included with Gaia, then include a 'gaia.cfg' properties file with your package along with a 'get_config' method in your package's __init__.py file to load the file's configuration properties.


Official Gaia Plugins
-----------------

- gaia-spatialstats-plugin_
- gaia-twitter-plugin_

.. _gaia-spatialstats-plugin: http://gaia-spatialstats-plugin.readthedocs.io/
.. _gaia-twitter-plugin: http://gaia-twitter-plugin.readthedocs.io/
