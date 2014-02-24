from distutils.core import setup, Command
import sys
import os
import argparse
import ConfigParser
from subprocess import check_call
import shutil
import os
import tempfile
import tarfile


VERSION = '0.07.1b'


class UninstallCommand(Command):
    description = "information on how to uninstall PyGeo"
    user_options = []

    def initialize_options(self): pass

    def finalize_options(self): pass

    def run(self):
        try:
            import pygeo
            print('To uninstall, manually remove the Python package folder located here: {0}'.format(os.path.split(pygeo.__file__)[0]))
        except ImportError:
            raise(ImportError("Either PyGeo is not installed or not available on the Python path."))
## check python version
python_version = float(sys.version_info[0]) + float(sys.version_info[1])/10
if python_version != 2.7:
    raise(ImportError(
        'This software requires Python version 2.7.x. You have {0}.x'.format(python_version)))

## attempt package imports
pkgs = []
for pkg in pkgs:
    try:
        __import__(pkg)
    except ImportError:
        msg = 'Unable to import required Python package: "{0}".'.format(pkg)
        raise(ImportError(msg))

## get package structure
def _get_dot_(path,root='src'):
    ret = []
    path_parse = path
    while True:
        path_parse,tail = os.path.split(path_parse)
        if tail == root:
            break
        else:
            ret.append(tail)
    ret.reverse()
    return('.'.join(ret))
package_dir = {'':'src'}
src_path = os.path.join(package_dir.keys()[0],package_dir.values()[0],'pygeo')
packages = []
for dirpath,dirnames,filenames in os.walk(src_path):
    if '__init__.py' in filenames:
        package = _get_dot_(dirpath)
        packages.append(package)

## run the installation
setup(name='pygeo',
      version=VERSION,
      author='Kitware',
      author_email='aashish.chaudhary@kitware.com',
      url='http://www.kitware.com',
      license='BSD license',
      platforms=['all'],
      packages=packages,
      package_dir=package_dir,
      cmdclass={'uninstall':UninstallCommand}
      )
