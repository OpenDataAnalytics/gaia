"""OpenSSL utilities module - contains OpenSSLConfig class for
parsing OpenSSL configuration files

NERC Data Grid Project
"""
__author__ = "P J Kershaw"
__date__ = "08/02/07"
__copyright__ = "(C) 2009 Science and Technology Facilities Council"
__license__ = """BSD - See LICENSE file in top-level directory"""
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__revision__ = '$Id:openssl.py 4643 2008-12-15 14:53:53Z pjkersha $'
import re
import os
from ConfigParser import SafeConfigParser


class OpenSSLConfigError(Exception):
    """Exceptions related to OpenSSLConfig class"""


class OpenSSLConfig(SafeConfigParser, object):
    """Wrapper to OpenSSL Configuration file to allow extraction of
    required distinguished name used for making certificate requests

    @type _certReqDNParamName: tuple
    @cvar _certReqDNParamName: permissable keys for Distinguished Name
    (not including CN which gets set separately).  This is used in _setReqDN
    to check input

    @type _caDirPat: string
    @cvar _caDirPat: sub-directory path to CA config directory
    @type _gridCASubDir: string
    @cvar _gridCASubDir: sub-directory of globus user for CA settings"""

    _certReqDNParamName = (
        'countryName',
        'C',
        'stateOrProvinceName',
        'ST',
        'localityName',
        'L'
        'organizationName',
        'O',
        'organizationalUnitName',
        'OU',
        'commonName',
        'CN',
        'emailAddress'
    )

    _caDirPat = re.compile('\$dir')
    _gridCASubDir = os.path.join(".globus", "simpleCA")

    def __init__(self, filePath=None, caDir=None):
        """Initial OpenSSL configuration optionally setting a file path to
        read from

        @type filePath: string
        @param filePath: path to OpenSSL configuration file

        @type caDir: string
        @param caDir: directory for SimpleCA.  This is substituted for $dir
        in OpenSSL config file where present.  caDir can be left out in
        which case the substitution is not done"""

        SafeConfigParser.__init__(self)

        self._reqDN = None
        self._setFilePath(filePath)

        # Set-up CA directory
        self.setCADir(caDir)


    def _setFilePath(self, filePath):
        """Set property method
        @type filePath: string
        @param filePath: path for OpenSSL configuration file"""
        if filePath is not None:
            if not isinstance(filePath, basestring):
                raise OpenSSLConfigError("Input OpenSSL config file path must "
                                         "be a string")

            try:
                if not os.access(filePath, os.R_OK):
                    raise OpenSSLConfigError("Not found or no read access")

            except Exception, e:
                raise OpenSSLConfigError("OpenSSL config file path is not "
                                         'valid: "%s": %s' % (filePath, e))

        self._filePath = filePath

    def _getFilePath(self):
        """Get property method
        @rtype: string
        @return: file path for OpenSSL configuration file"""
        return self.__filePath

    filePath = property(fget=_getFilePath,
                        fset=_setFilePath,
                        doc="file path for configuration file")

    def setCADir(self, caDir):
        """Set property method
        @type caDir: string
        @param caDir: path for OpenSSL configuration file"""
        if caDir is None:
            # Try to set default from 'HOME' env variable
            homeDir = os.environ.get('HOME')
            if homeDir:
                self._caDir = os.path.join(homeDir, self._gridCASubDir)
            else:
                self._caDir = None
        else:
            if not isinstance(caDir, basestring):
                raise OpenSSLConfigError("Input OpenSSL CA directory path "
                                         "must be a string")

            try:
                if not os.access(caDir, os.R_OK):
                    raise OpenSSLConfigError("Not found or no read access")

            except Exception, e:
                raise OpenSSLConfigError("OpenSSL CA directory path is not "
                                         'valid: "%s": %s' % (caDir, e))

        self._caDir = caDir

    def _getCADir(self):
        """Get property method
        @rtype caDir: string
        @return caDir: directory path for CA configuration files"""
        return self._caDir

    caDir = property(fget=_getCADir,
                     fset=setCADir,
                     doc="directory path for CA configuration files")

    def _getReqDN(self):
        """Get property method
        @rtype reqDN: dict
        @return reqDN: Distinguished Name for certificate request"""
        return self._reqDN

    def _setReqDN(self, reqDN):
        """Set property method
        @type reqDN: dict
        @param reqDN: Distinguished Name for certificate request"""
        if not isinstance(reqDN, dict):
            raise AttributeError("Distinguished Name must be dict type")

        invalidKw = [k for k in dict \
                     if k not in OpenSSLConfig._certReqDNParamName]
        if invalidKw:
            raise AttributeError("Invalid certificate request keyword(s): "
                                 "%s.  Valid keywords are: %s" %
                                 (', '.join(invalidKw),
                                 ', '.join(OpenSSLConfig._certReqDNParamName)))

        self._reqDN = reqDN

    reqDN = property(fget=_getReqDN,
                     fset=_setReqDN,
                     doc="Distinguished Name for certificate request")

    def read(self):
        """Override base class version to avoid parsing error with the first
        'RANDFILE = ...' part of the openssl file.  Also, reformat _sections
        to allow for the style of SSL config files where section headings can
        have spaces either side of the brackets e.g.
        [ sectionName ]

        and comments can occur on the same line as an option e.g.
        option = blah # This is option blah

        Reformat _sections to """
        try:
            file = open(self._filePath)
            fileTxt = file.read()
        except Exception, e:
            raise OpenSSLConfigError('Reading OpenSSL config file "%s": %s' %
                                                    (self._filePath, e))

        idx = re.search('\[\s*\w*\s*\]', fileTxt).span()[0]
        file.seek(idx)
        SafeConfigParser.readfp(self, file)

        # Filter section names and remove comments from options
        for section, val in self._sections.items():
            newSection = section
            self._sections[newSection.strip()] = \
                                    dict([(opt, self._filtOptVal(optVal))
                                          for opt, optVal in val.items()])
            del self._sections[section]

        self._set_required_dn_params()

    def _filtOptVal(self, optVal):
        """For option value, filter out comments and substitute $dir with
        the CA directory location

        @type optVal: string
        @param optVal: option value"""
        filtVal = optVal.split('#')[0].strip()
        if self._caDir:
            # Replace $dir with CA directory path
            return OpenSSLConfig._caDirPat.sub(self._caDir, filtVal)
        else:
            # Leave $dir in place as no CA directory has been set
            return filtVal

    def readfp(self, fp):
        """Set to not implemented as using a file object could be problematic
        given read() has to seek ahead to the first actual section to avoid
        parsing errors"""
        raise NotImplementedError("Use read method instead")

    def _set_required_dn_params(self):
        """Set Required DN parameters from the configuration file returning
        them in a dictionary"""

        # Nb. Match over line boundaries
        try:
            self._reqDN = {
                'O': self.get('req_distinguished_name',
                              '0.organizationName_default'),
                'OU': self.get('req_distinguished_name',
                               '0.organizationalUnitName_default')
            }
        except Exception, e:
            raise OpenSSLConfigError('Setting content of Distinguished Name '
                                     'from file "%s": %s' % (self._filePath, e))