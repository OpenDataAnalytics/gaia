#!/usr/bin/python

import pymongo

# Import Python modules
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
pygeo_dir = os.path.join(current_dir, "../../")
sys.path.append(pygeo_dir)

import pygeo
from pygeo.time.standardtime import attrib_to_converters

class mongo_import:
    def __init__(self, server, database):
        self._connection = pymongo.Connection(server)
        self._db = self._connection[database]

    def import_file(self, collection, filename, private=True):
        """Import metadata from a filename into the database

        This method reads a filename (fullpath) for its metadata
        and stores it into the specified collection of the database.

        :param collection: Name of the collection to look for basename.
        :type collection: str.
        :param filename: Name of the file with fullpath (eg. /home/clt.nc).
        :type filename: str.
        :param private: Should the entry be marked as private.
        :type private: bool
        """
        if (not (os.path.isfile(filename) and os.path.exists(filename))):
            raise Exception("File " + filename + " does not exist")

        # @note Assuming that getting mongo collection everytime
        # is not going to cause much performance penalty
        coll = self._db[collection]

        print 'Begin importing %s into database' % filename
        variables = []
        basename = os.path.basename(filename)
        filenamesplitted = os.path.splitext(basename)
        fileprefix = filenamesplitted[0]
        filesuffix = filenamesplitted[1]

        if self.is_exists(collection, filename):
          print 'Data  %s already exists' % filename
          return

        if filesuffix == ".nc":
            # VTK is required
            import vtk
            reader = vtk.vtkNetCDFCFReader()
            reader.SphericalCoordinatesOff()
            reader.SetOutputTypeToImage()
            reader.ReplaceFillValueWithNanOn()
            reader.SetFileName(filename)
            reader.Update()
            data = reader.GetOutput()

            # Obtain spatial information
            bounds = data.GetBounds()

            # Obtain temporal information
            timeInfo = {}
            times = reader.GetOutputInformation(0).Get(vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS())
            timeInfo['rawTimes'] = times #time steps in raw format
            tunits = reader.GetTimeUnits()
            timeInfo['units'] = tunits #calendar info needed to interpret/convert times
            converters = attrib_to_converters(tunits)
            if converters and times:
               timeInfo['numSteps'] = len(times)

               nativeStart = converters[3]
               timeInfo['nativeStart'] = nativeStart
               stepUnits = converters[2]
               timeInfo['nativeUnits'] = stepUnits
               stepSize = 0
               if len(times) > 1:
                 stepSize = times[1]-times[0]
               timeInfo['nativeDelta'] = stepSize
               stdTimeRange = (converters[0](times[0]), converters[0](times[-1]))
               timeInfo['nativeRange'] = (times[0], times[-1])

               stdTimeDelta = 0
               if len(times) > 1:
                   stdTimeDelta = converters[0](times[1]) - converters[0](times[0])
               timeInfo['stdDelta'] = stdTimeDelta
               stdTimeRange = (converters[0](times[0]), converters[0](times[-1]))
               timeInfo['stdTimeRange'] = stdTimeRange #first and last time as normalized integers

               dateRange = (converters[1](stdTimeRange[0]), converters[1](stdTimeRange[1]))
               timeInfo['dateRange'] = dateRange #first and last time in Y,M,D format

            # Obtain array information
            pds = data.GetPointData()
            pdscount = pds.GetNumberOfArrays()
            if times == None:
               times = [0]
            # Go through all timesteps to accumulate global min and max values
            for t in times:
               firstTStep = t==times[0]
               arrayindex = 0
               # Go through all arrays
               for i in range(0, pdscount):
                   pdarray = pds.GetArray(i)
                   if not pdarray:
                       # Got an abstract array
                       continue
                   if firstTStep:
                       # Create new record for this array
                       variable = {}
                   else:
                       # Extend existing record
                       variable = variables[arrayindex]
                   # Tell reader to read data so that we can get info about this time step
                   sddp = reader.GetExecutive()
                   sddp.SetUpdateTimeStep(0,t)
                   sddp.Update()
                   arrayindex = arrayindex + 1
                   if firstTStep:
                       # Record unchanging meta information
                       variable["name"] = pdarray.GetName()
                       variable["dim"] = []
                       variable["tags"] = []
                       variable["units"] = reader.QueryArrayUnits(pdarray.GetName())
                   # Find min and max for each component of this array at this timestep
                   componentCount = pdarray.GetNumberOfComponents()
                   minmax = []
                   for j in range(0, componentCount):
                       minmaxJ = [0,-1]
                       pdarray.GetRange(minmaxJ, j)
                       minmax.append(minmaxJ[0])
                       minmax.append(minmaxJ[1])
                   if firstTStep:
                       # Remember what we learned about this new array
                       variable["range"] = minmax
                       variables.append(variable)
                   else:
                       # Extend range if necessary from this timesteps range
                       for j in range(0, componentCount):
                           if minmax[j*2+0] < variable["range"][j*2+0]:
                               variable["range"][j*2+0] = minmax[j*2+0]
                           if minmax[j*2+1] > variable["range"][j*2+1]:
                               variable["range"][j*2+1] = minmax[j*2+1]

            # Record what we've learned in the data base
            insertId = coll.insert({"name":fileprefix, "basename":filename,
                                   "variables":variables,
                                   "timeInfo":timeInfo,
                                   "spatialInfo":bounds,
                                   "private":private})
        print 'Done importing %s into database' % filename

    def import_directory(self, collection, directory, drop_existing=False):
        """Import metadata from files of a directory into the database

        This method reads all of the files that belong to a directory
        for its metadata and stores it into the specified collection of
        the database.

        :param collection: Name of the collection to look for basename.
        :type collection: str.
        :param directory: Full path to the directory.
        :type directory: str.
        """
        if (not (os.path.isdir(directory) and os.path.exists(directory))):
          raise Exception("Directory " + directory + " does not exist")

        # Gather all files in the directory
        from os import listdir
        from os.path import isfile, join
        files = [f for f in listdir(directory) if isfile(join(directory,f))]

        # Check if requested to drop existing collection
        if drop_existing:
            self._db.drop_collection(collection)

        # Add files to the database
        for filename in files:
            self.import_file(collection, os.path.join(directory, filename), False)

    def is_exists(self, collection, basename):
        """Check if a basename exists in the given collection of the database.

        :param collection: Name of the collection to look for basename.
        :type collection: str.
        :param basename: Name of the file (eg. clt.nc).
        :type basename: str.
        :returns:  bool -- True if exists False otherwise.
        """
        if self._connection and self._db:
            coll = self._db[collection]
            if (coll.find({"basename": basename}).count() > 0):
                return True
        else:
            print 'Invalid connection'

        return False

if __name__ == "__main__":
    import sys
    print sys.argv
    if (len(sys.argv) < 5):
        print "usage: import_data server database collection directory"
        sys.exit(1)

    server = sys.argv[1]
    database = sys.argv[2]
    coll = sys.argv[3]
    directory = sys.argv[4]

    ins = mongo_import(server, database)
    ins.import_directory(coll, directory, True)
