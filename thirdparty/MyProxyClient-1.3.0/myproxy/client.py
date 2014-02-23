"""MyProxy Client interface

Developed for the NERC DataGrid Project: http://ndg.nerc.ac.uk/

Major re-write of an original class.   This updated version implements methods
with SSL calls with PyOpenSSL rather use calls to myproxy client executables as
in the original.  This version is adapted and extended from an original
program myproxy_logon by Tom Uram <turam@mcs.anl.gov>
"""
__author__ = "P J Kershaw"
__date__ = "02/06/05"
__copyright__ = "(C) 2010 Science and Technology Facilities Council"
__license__ = """BSD - See LICENSE file in top-level directory

For myproxy_logon see Access Grid Toolkit Public License (AGTPL)

This product includes software developed by and/or derived from the Access
Grid Project (http://www.accessgrid.org) to which the U.S. Government retains
certain rights."""
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__revision__ = '$Id: client.py 7928 2011-08-12 13:16:26Z pjkersha $'
import logging
log = logging.getLogger(__name__)

import sys
import os
import socket
import base64
import re
import traceback
import errno

from OpenSSL import crypto, SSL

from myproxy.utils.openssl import OpenSSLConfig
from myproxy.utils import CaseSensitiveConfigParser


class MyProxyServerSSLCertVerification(object):
    """Check MyProxy server identity.  If hostname doesn't match, allow match of
    host's Distinguished Name against MYPROXY_SERVER_DN setting"""
    DN_LUT = {
        'commonName':               'CN',
        'organisationalUnitName':   'OU',
        'organisation':             'O',
        'countryName':              'C',
        'emailAddress':             'EMAILADDRESS',
        'localityName':             'L',
        'stateOrProvinceName':      'ST',
        'streetAddress':            'STREET',
        'domainComponent':          'DC',
        'userid':                   'UID'
    }
    PARSER_RE_STR = '/(%s)=' % '|'.join(DN_LUT.keys() + DN_LUT.values())
    PARSER_RE = re.compile(PARSER_RE_STR)
    SERVER_CN_PREFIXES = ('host/', 'myproxy/', '')

    SERVER_CN_PREFIX = 'host/'

    __slots__ = ('__hostname', '__certDN')

    def __init__(self, certDN=None, hostname=None):
        """Override parent class __init__ to enable setting of certDN
        setting

        @type certDN: string
        @param certDN: Set the expected Distinguished Name of the
        MyProxy server to avoid errors matching hostnames.  This is useful
        where the hostname is not fully qualified
        """
        self.__certDN = None
        self.__hostname = None

        if certDN is not None:
            self.certDN = certDN

        if hostname is not None:
            self.hostname = hostname

    def __call__(self, connection, peerCert, errorStatus, errorDepth,
                 preverifyOK):
        """Verify MyProxy server certificate

        @type connection: OpenSSL.SSL.Connection
        @param connection: SSL connection object
        @type peerCert: basestring
        @param peerCert: MyProxy server host certificate as OpenSSL.crypto.X509
        instance
        @type errorStatus: int
        @param errorStatus: error status passed from caller.  This is the value
        returned by the OpenSSL C function X509_STORE_CTX_get_error().  Look-up
        x509_vfy.h in the OpenSSL source to get the meanings of the different
        codes.  PyOpenSSL doesn't help you!
        @type errorDepth: int
        @param errorDepth: a non-negative integer representing where in the
        certificate chain the error occurred. If it is zero it occured in the
        end entity certificate, one if it is the certificate which signed the
        end entity certificate and so on.

        @type preverifyOK: int
        @param preverifyOK: the error status - 0 = Error, 1 = OK of the current
        SSL context irrespective of any verification checks done here.  If this
        function yields an OK status, it should enforce the preverifyOK value
        so that any error set upstream overrides and is honoured.
        @rtype: int
        @return: status code - 0/False = Error, 1/True = OK
        """
        if peerCert.has_expired():
            # Any expired certificate in the chain should result in an error
            log.error('Certificate %r in peer certificate chain has expired',
                      peerCert.get_subject())

            return False

        elif errorDepth == 0:
            # Only interested in DN of last certificate in the chain - this must
            # match the expected MyProxy Server DN setting
            peerCertSubj = peerCert.get_subject()
            peerCertDN = peerCertSubj.get_components()
            peerCertDN.sort()

            if self.certDN is None:
                # Check hostname against peer certificate CN field instead:
                if self.hostname is None:
                    log.error('No "hostname" or "certDN" set to check peer '
                              'certificate against')
                    return False

                acceptableCNs = [pfx + self.hostname
                                 for pfx in self.__class__.SERVER_CN_PREFIXES]
                if peerCertSubj.commonName in acceptableCNs:
                    return preverifyOK
                else:
                    log.error('Peer certificate CN %r doesn\'t match the '
                              'expected CN %r', peerCertSubj.commonName,
                              acceptableCNs)
                    return False
            else:
                if peerCertDN == self.certDN:
                    return preverifyOK
                else:
                    log.error('Peer certificate DN %r doesn\'t match the '
                              'expected DN %r', peerCertDN, self.certDN)
                    return False
        else:
            return preverifyOK

    def _getCertDN(self):
        return self.__certDN

    def _setCertDN(self, val):
        if isinstance(val, basestring):
            # Allow for quoted DN
            certDN = val.strip('"')

            dnFields = self.__class__.PARSER_RE.split(certDN)
            if len(dnFields) < 2:
                raise TypeError('Error parsing DN string: "%s"' % certDN)

            self.__certDN = zip(dnFields[1::2], dnFields[2::2])
            self.__certDN.sort()

        elif not isinstance(val, list):
            for i in val:
                if not len(i) == 2:
                    raise TypeError('Expecting list of two element DN field, '
                                    'DN field value pairs for "certDN" '
                                    'attribute')
            self.__certDN = val
        else:
            raise TypeError('Expecting list or string type for "certDN" '
                            'attribute')

    certDN = property(fget=_getCertDN,
                      fset=_setCertDN,
                      doc="Distinguished Name for MyProxy Server Certificate")

    # Get/Set Property methods
    def _getHostname(self):
        return self.__hostname

    def _setHostname(self, val):
        if not isinstance(val, basestring):
            raise TypeError("Expecting string type for hostname "
                                 "attribute")
        self.__hostname = val

    hostname = property(fget=_getHostname,
                        fset=_setHostname,
                        doc="hostname of MyProxy server")


class MyProxyClientError(Exception):
    """Base exception class for MyProxyClient exceptions"""


class MyProxyClientConfigError(MyProxyClientError):
    """Error with configuration"""


class MyProxyClientGetError(MyProxyClientError):
    """Exceptions arising from get request to server"""


class MyProxyClientRetrieveError(MyProxyClientError):
    """Error recovering a response from MyProxy"""


class MyProxyCredentialsAlreadyExist(MyProxyClientError):
    """Attempting to upload credentials to the server which already exist.  -
    See MyProxyClient.store
    """


class MyProxyClientGetTrustRootsError(MyProxyClientError):
    """Error retrieving trust roots"""


class MyProxyClient(object):
    """MyProxy client interface

    Based on protocol definitions in:

    http://grid.ncsa.uiuc.edu/myproxy/protocol/

    @type MYPROXY_SERVER_ENVVARNAME: string
    @cvar MYPROXY_SERVER_ENVVARNAME: server environment variable name

    @type MYPROXY_SERVER_PORT_ENVVARNAME: string
    @cvar MYPROXY_SERVER_PORT_ENVVARNAME: port environment variable name

    @type MYPROXY_SERVER_DN_ENVVARNAME: string
    @cvar MYPROXY_SERVER_DN_ENVVARNAME: server certificate Distinguished Name
    environment variable name

    @type GLOBUS_LOCATION_ENVVARNAME: string
    @param GLOBUS_LOCATION_ENVVARNAME: 'GLOBUS_LOCATION' environment variable
    name

    @type GET_CMD: string
    @cvar GET_CMD: get command string

    @type INFO_CMD: string
    @cvar INFO_CMD: info command string

    @type DESTROY_CMD: string
    @cvar DESTROY_CMD: destroy command string

    @type CHANGE_PASSPHRASE_CMD: string
    @cvar CHANGE_PASSPHRASE_CMD: command string to change cred pass-phrase

    @type STORE_CMD: string
    @cvar STORE_CMD: store command string

    @type GET_TRUST_ROOTS_CMD: string
    @cvar GET_TRUST_ROOTS_CMD: get trust roots command string

    @type TRUSTED_CERTS_FIELDNAME: string
    @param TRUSTED_CERTS_FIELDNAME: field name in get trust roots response for
    trusted certificate file names

    @type TRUSTED_CERTS_FILEDATA_FIELDNAME_PREFIX: string
    @param TRUSTED_CERTS_FILEDATA_FIELDNAME_PREFIX: field name prefix in get
    trust roots response for trusted certificate file contents

    @type HOSTCERT_SUBDIRPATH: string
    @cvar HOSTCERT_SUBDIRPATH: sub-directory path host certificate (as tuple)

    @type HOSTKEY_SUBDIRPATH: string
    @cvar HOSTKEY_SUBDIRPATH: sub-directory path to host key (as tuple)

    @type PRIKEY_NBITS: int
    @cvar PRIKEY_NBITS: default number of bits for private key generated

    @type MESSAGE_DIGEST_TYPE: string
    @cvar MESSAGE_DIGEST_TYPE: message digest type is MD5

    @type SERVER_RESP_BLK_SIZE: int
    @cvar SERVER_RESP_BLK_SIZE: block size for retrievals from server

    @type MAX_RECV_TRIES: int
    @cvar MAX_RECV_TRIES: maximum number of retrievals of size
    SERVER_RESP_BLK_SIZE before this client gives up

    @type DEF_PROXY_FILEPATH: string
    @cvar DEF_PROXY_FILEPATH: default location for proxy file to be written to

    @type PROXY_FILE_PERMISSIONS: int
    @cvar PROXY_FILE_PERMISSIONS: file permissions returned proxy file is
    created with

    @type PROPERTY_DEFAULTS: tuple
    @cvar PROPERTY_DEFAULTS: sets permissable element names for MyProxy config
    file

    @type ROOT_USERNAME: string
    @cvar ROOT_USERNAME: root username - used to determine output directory
    for trust roots

    @type ROOT_TRUSTROOT_DIR: string
    @param ROOT_TRUSTROOT_DIR: default trust root directory if running as root
    user

    @type USER_TRUSTROOT_DIR: string
    @param USER_TRUSTROOT_DIR: default trust root directory for users other
    than root

    @type X509_CERT_DIR_ENVVARNAME: string
    @param X509_CERT_DIR_ENVVARNAME: environment variable name 'X509_CERT_DIR',
    which if set points to the location of the trust roots

    @type X509_USER_PROXY_ENVVARNAME: string
    @param X509_USER_PROXY_ENVVARNAME: environment variable name
    'X509_USER_PROXY' if set points to the output location of the output EEC /
    Proxy certificate.  Not currently used by this class, included for
    reference only
    """
    MYPROXY_SERVER_ENVVARNAME = 'MYPROXY_SERVER'
    MYPROXY_SERVER_PORT_ENVVARNAME = 'MYPROXY_SERVER_PORT'
    MYPROXY_SERVER_DN_ENVVARNAME = 'MYPROXY_SERVER_DN'

    GLOBUS_LOCATION_ENVVARNAME = 'GLOBUS_LOCATION'
    X509_USER_PROXY_ENVVARNAME = 'X509_USER_PROXY'

    GET_CMD="""VERSION=MYPROXYv2
COMMAND=0
USERNAME=%s
PASSPHRASE=%s
LIFETIME=%d"""

    PUT_CMD="""VERSION=MYPROXYv2
COMMAND=1
USERNAME=%s
PASSPHRASE=<pass phrase>
LIFETIME=%d"""

    INFO_CMD="""VERSION=MYPROXYv2
COMMAND=2
USERNAME=%s
PASSPHRASE=PASSPHRASE
LIFETIME=0"""

    DESTROY_CMD="""VERSION=MYPROXYv2
COMMAND=3
USERNAME=%s
PASSPHRASE=PASSPHRASE
LIFETIME=0"""

    CHANGE_PASSPHRASE_CMD="""VERSION=MYPROXYv2
 COMMAND=4
 USERNAME=%s
 PASSPHRASE=%s
 NEW_PHRASE=%s
 LIFETIME=0"""

    STORE_CMD="""VERSION=MYPROXYv2
COMMAND=5
USERNAME=%s
PASSPHRASE=
LIFETIME=%d"""

    GET_TRUST_ROOTS_CMD="""VERSION=MYPROXYv2
COMMAND=7
USERNAME=%s
PASSPHRASE=%s
LIFETIME=0
TRUSTED_CERTS=1"""

    TRUSTED_CERTS_FIELDNAME = 'TRUSTED_CERTS'
    TRUSTED_CERTS_FILEDATA_FIELDNAME_PREFIX = 'FILEDATA_'

    HOSTCERT_FILENAME = 'hostcert.pem'
    HOSTKEY_FILENAME = 'hostkey.pem'

    GRID_SECURITY_DIRPATH = '/etc/grid-security'

    HOSTCERT_GRID_FILEPATH = os.path.join(GRID_SECURITY_DIRPATH,
                                          HOSTCERT_FILENAME)
    HOSTKEY_GRID_FILEPATH = os.path.join(GRID_SECURITY_DIRPATH,
                                         HOSTKEY_FILENAME)

    HOSTCERT_SUBDIRPATH = ('etc', HOSTCERT_FILENAME)
    HOSTKEY_SUBDIRPATH = ('etc', HOSTKEY_FILENAME)

    PROXY_FILE_PERMISSIONS = 0600

    # Work out default location of proxy file if it exists.  This is set if a
    # call has been made previously to logon / get-delegation
    DEF_PROXY_FILEPATH = sys.platform == ('win32' and 'proxy' or
                                    sys.platform in ('linux2', 'darwin') and
                                    '/tmp/x509up_u%s' % (os.getuid())
                                    or None)

    PRIKEY_NBITS = 4096
    MESSAGE_DIGEST_TYPE = "md5"
    SERVER_RESP_BLK_SIZE = 8192
    MAX_RECV_TRIES = 1024

    # valid configuration property keywords
    PROPERTY_DEFAULTS = {
       'hostname':              'localhost',
       'port':                  7512,
       'serverDN':              None,
       'openSSLConfFilePath':   '',
       'proxyCertMaxLifetime':  43200,
       'proxyCertLifetime':     43200,
       'caCertDir':             None
    }

    ROOT_USERNAME = 'root'
    ROOT_TRUSTROOT_DIR = '/etc/grid-security/certificates'
    USER_TRUSTROOT_DIR = '~/.globus/certificates'
    X509_CERT_DIR_ENVVARNAME = 'X509_CERT_DIR'
    X509_USER_PROXY_ENVVARNAME = 'X509_USER_PROXY'

    # Restrict attributes to the above properties, their equivalent
    # protected values + extra OpenSSL config object.
    __slots__ = tuple(['__' + k for k in PROPERTY_DEFAULTS.keys()])
    del k
    __slots__ += ('__openSSLConfig', '__cfg', '__serverSSLCertVerify')

    def __init__(self, cfgFilePath=None, **prop):
        """Make any initial settings for client connections to MyProxy

        Settings are held in a dictionary which can be set from **prop,
        a call to setProperties() or by passing settings in an XML file
        given by cfgFilePath

        @param cfgFilePath: set properties via a configuration file
        @type cfgFilePath: basestring
        @param **prop: set properties via keywords - see
        PROPERTY_DEFAULTS class variable for a list of these
        @type **prop: dict
        """
        self.__serverSSLCertVerify = MyProxyServerSSLCertVerification()
        self.__hostname = None
        self.__port = None
        self.__serverDN = None
        self.__openSSLConfFilePath = None
        self.__proxyCertMaxLifetime = MyProxyClient.PROPERTY_DEFAULTS[
                                                        'proxyCertMaxLifetime']
        self.__proxyCertLifetime = MyProxyClient.PROPERTY_DEFAULTS[
                                                        'proxyCertLifetime']
        self.__caCertDir = None

        self.__cfg = None

        # Configuration file used to get default subject when generating a
        # new proxy certificate request
        self.__openSSLConfig = OpenSSLConfig()

        # Server host name - take from environment variable if available
        self.hostname = os.environ.get(MyProxyClient.MYPROXY_SERVER_ENVVARNAME,
                                    MyProxyClient.PROPERTY_DEFAULTS['hostname'])

        # ... and port number
        self.port = int(os.environ.get(
                                MyProxyClient.MYPROXY_SERVER_PORT_ENVVARNAME,
                                MyProxyClient.PROPERTY_DEFAULTS['port']))

        # Server Distinguished Name
        serverDN = os.environ.get(MyProxyClient.MYPROXY_SERVER_DN_ENVVARNAME,
                                  MyProxyClient.PROPERTY_DEFAULTS['serverDN'])
        if serverDN is not None:
            self.serverDN = serverDN

        # Set trust root - the directory containing the CA certificates for
        # verifying the MyProxy server's SSL certificate
        self.setDefaultCACertDir()

        # Any keyword settings override the defaults above
        for opt, val in prop.items():
            setattr(self, opt, val)

        # If properties file is set any parameters settings in file will
        # override those set by input keyword or the defaults
        if cfgFilePath is not None:
            self.parseConfig(cfg=cfgFilePath)

    def setDefaultCACertDir(self):
        '''Make default trust root setting - the directory containing the CA
        certificates for verifying the MyProxy server's SSL certificate.

        The setting is made by using standard Globus defined locations and
        environment variable settings
        '''

        # Check for X509_CERT_DIR environment variable
        x509CertDir = os.environ.get(MyProxyClient.X509_CERT_DIR_ENVVARNAME)
        if x509CertDir is not None:
            self.caCertDir = x509CertDir

        # Check for running as root user
        elif os.environ.get(MyProxyClient.ROOT_USERNAME) is not None:
            self.caCertDir = MyProxyClient.ROOT_TRUSTROOT_DIR

        # Default to non-root standard location
        else:
            self.caCertDir = os.path.expanduser(
                                            MyProxyClient.USER_TRUSTROOT_DIR)

    def _getServerSSLCertVerify(self):
        return self.__serverSSLCertVerify

    def _setServerSSLCertVerify(self, value):
        if not isinstance(value, MyProxyServerSSLCertVerification):
            raise TypeError('Expecting %r derived type for '
                            '"serverSSLCertVerify" attribute; got %r' %
                            MyProxyServerSSLCertVerification,
                            value)
        self.__serverSSLCertVerify = value

    serverSSLCertVerify = property(_getServerSSLCertVerify,
                                   _setServerSSLCertVerify,
                                   doc="Class with a __call__ method which is "
                                       "passed to the SSL context to verify "
                                       "the peer (MyProxy server) certificate "
                                       "in the SSL handshake between this "
                                       "client and the MyProxy server")

    def parseConfig(self, cfg, section='DEFAULT'):
        '''Extract parameters from _cfg config object'''

        if isinstance(cfg, basestring):
            cfgFilePath = os.path.expandvars(cfg)
            self.__cfg = CaseSensitiveConfigParser()
            self.__cfg.read(cfgFilePath)
        else:
            cfgFilePath = None
            self.__cfg = cfg

        for key, val in self.__cfg.items(section):
            setattr(self, key, val)

    # Get/Set Property methods
    def _getHostname(self):
        return self.__hostname

    def _setHostname(self, val):
        """Also sets SSL Certificate verification object property!"""
        if not isinstance(val, basestring):
            raise TypeError("Expecting string type for hostname "
                                 "attribute")
        self.__hostname = val
        self.__serverSSLCertVerify.hostname = val

    hostname = property(fget=_getHostname,
                        fset=_setHostname,
                        doc="hostname of MyProxy server")

    def _getPort(self):
        return self.__port

    def _setPort(self, val):
        if isinstance(val, basestring):
            self.__port = int(val)
        elif isinstance(val, int):
            self.__port = val
        else:
            raise TypeError("Expecting int type for port attribute")

    port = property(fget=_getPort,
                    fset=_setPort,
                    doc="Port number for MyProxy server")

    def _getServerDN(self):
        return self.__serverDN

    def _setServerDN(self, val):
        """Also sets SSL Certificate verification object property!"""
        if not isinstance(val, basestring):
            raise TypeError("Expecting string type for serverDN attribute")

        self.__serverDN = val
        self.__serverSSLCertVerify.certDN = val

    serverDN = property(fget=_getServerDN,
                        fset=_setServerDN,
                        doc="Distinguished Name for MyProxy Server "
                            "Certificate")

    def _getOpenSSLConfFilePath(self):
        return self.__openSSLConfFilePath

    def _setOpenSSLConfFilePath(self, val):
        if not isinstance(val, basestring):
            raise TypeError('Expecting string type for "openSSLConfFilePath" '
                            'attribute')

        self.__openSSLConfFilePath = os.path.expandvars(val)
        self.__openSSLConfig.filePath = self.__openSSLConfFilePath
        self.__openSSLConfig.read()

    openSSLConfFilePath = property(fget=_getOpenSSLConfFilePath,
                                   fset=_setOpenSSLConfFilePath,
                                   doc="file path for OpenSSL config file")

    def _getProxyCertMaxLifetime(self):
        return self.__proxyCertMaxLifetime

    def _setProxyCertMaxLifetime(self, val):
        if isinstance(val, basestring):
            self.__proxyCertMaxLifetime = int(val)

        elif isinstance(val, int):
            self.__proxyCertMaxLifetime = val
        else:
            raise TypeError("Expecting int type for proxyCertMaxLifetime "
                            "attribute")

    proxyCertMaxLifetime = property(fget=_getProxyCertMaxLifetime,
                                    fset=_setProxyCertMaxLifetime,
                                    doc="Default max. lifetime allowed for "
                                        "Proxy Certificate retrieved - used "
                                        "by store method")

    def _getProxyCertLifetime(self):
        return self.__proxyCertLifetime

    def _setProxyCertLifetime(self, val):
        if isinstance(val, (basestring, float)):
            self.__proxyCertLifetime = int(val)
        elif isinstance(val, int):
            self.__proxyCertLifetime = val
        else:
            raise TypeError("Expecting int, float or string type for input "
                            "proxyCertLifetime attribute")

    proxyCertLifetime = property(fget=_getProxyCertLifetime,
                                 fset=_setProxyCertLifetime,
                                 doc="Default proxy cert. lifetime (seconds) "
                                     "used in logon request")

    def _getCACertDir(self):
        return self.__caCertDir

    def _setCACertDir(self, val):
        '''Specify a directory containing PEM encoded CA certs. used for
        validation of MyProxy server certificate.

        Set to None to make OpenSSL.SSL.Context.load_verify_locations ignore
        this parameter

        @type val: basestring/None
        @param val: directory path'''

        if isinstance(val, basestring):
            if val == '':
                self.__caCertDir = None
            else:
                self.__caCertDir = os.path.expandvars(val)

        elif isinstance(val, None):
            self.__caCertDir = val
        else:
            raise TypeError("Expecting string or None type for caCertDir "
                            "attribute")

    caCertDir = property(fget=_getCACertDir,
                         fset=_setCACertDir,
                         doc="trust roots directory containing PEM encoded CA "
                             "certificates to validate MyProxy server "
                             "certificate")


    def _getOpenSSLConfig(self):
        "Get OpenSSLConfig object property method"
        return self.__openSSLConfig

    openSSLConfig = property(fget=_getOpenSSLConfig, doc="OpenSSLConfig object")

    def _initConnection(self,
                        certFile=None,
                        keyFile=None,
                        keyFilePassphrase=None,
                        verifyPeerWithTrustRoots=True):
        """Initialise connection setting up SSL context and client and
        server side identity checks

        @type sslCertFile: basestring
        @param sslCertFile: certificate for SSL client authentication.  It may
        be owner of a credential to be acted on or the concatenated proxy
        certificate + proxy's signing cert.  SSL client authentication is not
        necessary for getDelegation / logon calls
        @type sslKeyFile: basestring
        @param sslKeyFile: client private key file
        @type keyFilePassphrase: basestring
        @param keyFilePassphrase: pass-phrase protecting private key if set
        @type verifyPeerWithTrustRoots: bool
        @param verifyPeerWithTrustRoots: verify MyProxy server's SSL certificate
        against a list of trusted CA certificates in the CA certificate
        directory set by the "CaCertDir" attribute.  This should always be set
        to True for MyProxy client calls unless using the 'bootstrap' trust
        roots mode available with logon and get trust roots calls
        """
        # Must be version 3 for MyProxy
        context = SSL.Context(SSL.SSLv3_METHOD)

        if verifyPeerWithTrustRoots:
            context.load_verify_locations(None, self.caCertDir)

            # Verify peer's (MyProxy server) certificate
            context.set_verify(SSL.VERIFY_PEER, self.__serverSSLCertVerify)

        if certFile:
            try:
                context.use_certificate_chain_file(certFile)
                def pwdCallback(passphraseMaxLen,
                                promptPassphraseTwice,
                                passphrase):
                    """Private key file password callback function"""
                    if len(passphrase) > passphraseMaxLen:
                        log.error('Passphrase length %d is greater than the '
                                  'maximum length allowed %d',
                                  len(passphrase), passphraseMaxLen)
                        return ''

                    return passphrase

                if keyFilePassphrase is not None:
                    context.set_passwd_cb(pwdCallback, keyFilePassphrase)

                context.use_privatekey_file(keyFile)
            except Exception:
                raise MyProxyClientConfigError("Loading certificate "
                                               "and private key for SSL "
                                               "connection [also check CA "
                                               "certificate settings]: %s" %
                                               traceback.format_exc())

        # Disable for compatibility with myproxy server (er, globus)
        # globus doesn't handle this case, apparently, and instead
        # chokes in proxy delegation code
        context.set_options(SSL.OP_DONT_INSERT_EMPTY_FRAGMENTS)

        # connect to myproxy server
        conn = SSL.Connection(context, socket.socket())

        return conn

    def _createKeyPair(self, nBitsForKey=PRIKEY_NBITS):
        """Generate key pair and return as PEM encoded string
        @type nBitsForKey: int
        @param nBitsForKey: number of bits for private key generation -
        default is 2048
        @rtype: OpenSSL.crypto.PKey
        @return: public/private key pair
        """
        keyPair = crypto.PKey()
        keyPair.generate_key(crypto.TYPE_RSA, nBitsForKey)

        return keyPair

    def _createCertReq(self, CN, keyPair, messageDigest=MESSAGE_DIGEST_TYPE):
        """Create a certificate request.

        @type CN: basestring
        @param CN: Common Name for certificate - effectively the same as the
        username for the MyProxy credential
        @type keyPair: string/None
        @param keyPair: public/private key pair
        @type messageDigest: basestring
        @param messageDigest: message digest type - default is MD5
        @rtype: base string
        @return certificate request PEM text and private key PEM text
        """

        # Check all required certifcate request DN parameters are set
        # Create certificate request
        certReq = crypto.X509Req()

        # Create public key object
        certReq.set_pubkey(keyPair)

        # Add the public key to the request
        certReq.sign(keyPair, messageDigest)

        derCertReq = crypto.dump_certificate_request(crypto.FILETYPE_ASN1,
                                                     certReq)

        return derCertReq

    def _deserializeResponse(self, msg, *fieldNames):
        """
        Deserialize a MyProxy server response

        @param msg: string response message from MyProxy server
        @return: tuple of integer response and errorTxt string (if any) and all
        the fields parsed.  fields is a list of two element, field name, field
        value tuples.
        @rtype: tuple
        """
        lines = msg.split('\n')
        fields = [tuple(line.split('=', 1)) for line in lines][:-1]

        # get response value
        respCode = [int(v) for k, v in fields if k == 'RESPONSE'][0]

        # get error text
        errorTxt = os.linesep.join([v for k, v in fields if k == 'ERROR'])

        # Check for custom fields requested by caller to this method
        if fieldNames:
            fieldsDict = {}
            for k, v in fields:
                names = [name for name in fieldNames if k.startswith(name)]
                if len(names) == 0:
                    continue
                else:
                    if v.isdigit():
                        fieldsDict[k] = int(v)
                    else:
                        fieldsDict[k] = v

            # Return additional dict item in tuple
            return respCode, errorTxt, fieldsDict
        else:
            return respCode, errorTxt

    def _deserializeCerts(self, inputDat):
        """Unpack certificates returned from a get delegation call to the
        server

        @param inputDat: string containing the proxy cert and private key
        and signing cert all in DER format

        @return list containing the equivalent to the input in PEM format"""
        pemCerts = []
        dat = inputDat

        while dat:
            # find start of cert, get length
            ind = dat.find('\x30\x82')
            if ind < 0:
                break

            len = 256*ord(dat[ind+2]) + ord(dat[ind+3])

            # extract der-format cert, and convert to pem
            derCert = dat[ind:ind+len+4]
            x509Cert = crypto.load_certificate(crypto.FILETYPE_ASN1, derCert)
            pemCert = crypto.dump_certificate(crypto.FILETYPE_PEM, x509Cert)
            pemCerts.append(pemCert)

            # trim cert from data
            dat = dat[ind + len + 4:]

        return pemCerts

    @classmethod
    def locateClientCredentials(cls, enableTmpFileLoc=False):
        """Find the location of a client certificate and private key to use to
        authenticate with the server based on the various default locations
        that MyProxy/Globus support

        @param enableTmpFileLoc: enable setting based on /tmp/x509up_<uid>,
        defaults to False
        @type enableTmpFileLoc: bool
        @return: private key and certificate file location to use based on the
        current environment
        @rtype: tuple
        """
        sslKeyFile = None
        sslCertFile = None

        x509UserProxy = os.environ.get(cls.X509_USER_PROXY_ENVVARNAME)
        if x509UserProxy is not None:
            sslKeyFile = x509UserProxy
            sslCertFile = x509UserProxy

        elif enableTmpFileLoc and os.access(cls.DEF_PROXY_FILEPATH, os.R_OK):
            sslKeyFile = cls.DEF_PROXY_FILEPATH
            sslCertFile = cls.DEF_PROXY_FILEPATH

        elif (os.access(cls.HOSTKEY_GRID_FILEPATH, os.R_OK) and
              os.access(cls.HOSTCERT_GRID_FILEPATH, os.R_OK)):
            sslKeyFile = cls.HOSTKEY_GRID_FILEPATH
            sslCertFile = cls.HOSTCERT_GRID_FILEPATH

        else:
            globusLoc = os.environ.get(cls.GLOBUS_LOCATION_ENVVARNAME)
            if globusLoc:
                sslKeyFile = os.path.join(globusLoc,
                                          *cls.HOSTKEY_SUBDIRPATH)
                if os.access(sslKeyFile, os.R_OK):
                    sslCertFile = os.path.join(globusLoc,
                                           *cls.HOSTCERT_SUBDIRPATH)
                else:
                    # Access to the private key is prohibited default to
                    # username/password based authentication
                    sslKeyFile = None
                    sslCertFile = None

        return sslKeyFile, sslCertFile

    @classmethod
    def writeProxyFile(cls, proxyCert, proxyPriKey, userX509Cert,
                       filePath=None):
        """Write out proxy cert to file in the same way as myproxy-logon -
        proxy cert, private key, user cert.  Nb. output from logon can be
        passed direct into this method

        @type proxyCert: string
        @param proxyCert: proxy certificate
        @type proxyPriKey: string
        @param proxyPriKey: private key for proxy
        @type userX509Cert: string
        @param userX509Cert: user certificate which issued the proxy
        @type filePath: string
        @param filePath: set to override the default filePath"""

        if filePath is None:
            filePath = MyProxyClient.DEF_PROXY_FILEPATH

        if filePath is None:
            MyProxyClientConfigError("Error setting proxy file path - invalid "
                                     "platform?")

        outStr = proxyCert + proxyPriKey + userX509Cert
        open(MyProxyClient.DEF_PROXY_FILEPATH, 'w').write(outStr)
        try:
            # Make sure permissions are set correctly
            os.chmod(MyProxyClient.DEF_PROXY_FILEPATH,
                     MyProxyClient.PROXY_FILE_PERMISSIONS)
        except Exception, e:
            # Don't leave the file lying around if couldn't change it's
            # permissions
            os.unlink(MyProxyClient.DEF_PROXY_FILEPATH)

            log.error('Unable to set %o permissions for proxy file "%s": %s'%
                      (MyProxyClient.PROXY_FILE_PERMISSIONS,
                       MyProxyClient.DEF_PROXY_FILEPATH, e))
            raise

    @classmethod
    def readProxyFile(cls, filePath=None):
        """Read proxy cert file following the format used by myproxy-logon -
        proxy, cert, private key, user cert.

        @rtype: tuple
        @return: tuple containing proxy cert, private key, user cert"""
        if filePath is None:
            filePath = MyProxyClient.DEF_PROXY_FILEPATH

        if filePath is None:
            MyProxyClientConfigError("Error setting proxy file path - invalid "
                                     "platform?")

        proxy = open(MyProxyClient.DEF_PROXY_FILEPATH).read()

        # Split certs and key into separate tuple items
        return tuple(['-----BEGIN'+i for i in proxy.split('-----BEGIN')[1:]])

    def put(self,
            username,
            passphrase,
            userCertFile,
            userKeyFile,
            lifetime=None,
            sslCertFile=None,
            sslKeyFile=None,
            sslKeyFilePassphrase=None):
        """Store a proxy credential on the server

        Unfortunately this method is not implemented as it requires the creation
        of a proxy certificate by the client but PyOpenSSL doesn't currently
        support the required proxyCertInfo X.509 certificate extension

        @raise NotImplementedError: see above

        @type username: string
        @param username: username selected for new credential
        @type passphrase: string
        @param passphrase: pass-phrase for new credential.  This will be used
        by the server to authenticate later requests.  IT must be at least
        6 characters.  The server may impose other restrictions too depending
        on its configuration.
        @type certFile: string
        @param certFile: user's X.509 proxy certificate in PEM format
        @type keyFile: string
        @param keyFile: equivalent private key file in PEM format
        @type sslCertFile: string
        @param sslCertFile: certificate used for client authentication with
        the MyProxy server SSL connection.  If not set,
        this argument defaults to $GLOBUS_LOCATION/etc/hostcert.pem
        @type sslKeyFile: string
        @param sslKeyFile: corresponding private key file.  See explanation
        for sslCertFile
        @type sslKeyFilePassphrase: string
        @param sslKeyFilePassphrase: passphrase for sslKeyFile.  Omit if the
        private key is not password protected.
        @type lifetime: int / None
        @param lifetime: the maximum lifetime allowed for retrieved proxy
        credentials in seconds. defaults to proxyCertMaxLifetime attribute value
        """
        raise NotImplementedError('put method is not currently implemented.  '
                                  'It requires the creation of a proxy '
                                  'certificate by the client but PyOpenSSL '
                                  'doesn\'t currently support the required '
                                  'proxyCertInfo X.509 certificate extension.')

    def info(self,
             username,
             sslCertFile=None,
             sslKeyFile=None,
             sslKeyFilePassphrase=None):
        """return True/False whether credentials exist on the server for a
        given username

        @raise MyProxyClientGetError:
        @raise MyProxyClientRetrieveError:

        @type username: string
        @param username: username selected for credential
        @type sslCertFile: string
        @param sslCertFile: certificate used for client authentication with
        the MyProxy server SSL connection.  This ID will be set as the owner
        of the stored credentials.  Only the owner can later remove
        credentials with myproxy-destroy or the destroy method.  If not set,
        this argument defaults to $GLOBUS_LOCATION/etc/hostcert.pem
        @type sslKeyFile: string
        @param sslKeyFile: corresponding private key file.  See explanation
        for sslCertFile
        @type sslKeyFilePassphrase: string
        @param sslKeyFilePassphrase: passphrase for sslKeyFile.  Omit if the
        private key is not password protected.
        """
        globusLoc = os.environ.get(MyProxyClient.GLOBUS_LOCATION_ENVVARNAME)
        if not sslCertFile:
            if globusLoc:
                sslCertFile = os.path.join(globusLoc,
                                            *MyProxyClient.HOSTCERT_SUBDIRPATH)
                sslKeyFile = os.path.join(globusLoc,
                                            *MyProxyClient.HOSTKEY_SUBDIRPATH)
            else:
                raise MyProxyClientError(
            "No client authentication cert. and private key file were given")

        # Set-up SSL connection
        conn = self._initConnection(certFile=sslCertFile,
                                    keyFile=sslKeyFile,
                                    keyFilePassphrase=sslKeyFilePassphrase)

        conn.connect((self.hostname, self.port))

        # send globus compatibility stuff
        conn.write('0')

        # send info command - ensure conversion from unicode before writing
        cmd = MyProxyClient.INFO_CMD % username
        conn.write(str(cmd))

        # process server response
        dat = conn.recv(MyProxyClient.SERVER_RESP_BLK_SIZE)

        # Pass in the names of fields to return in the dictionary 'field'
        respCode, errorTxt, field = self._deserializeResponse(dat,
                                                              'CRED_START_TIME',
                                                              'CRED_END_TIME',
                                                              'CRED_OWNER')

        return not bool(respCode), errorTxt, field

    def changePassphrase(self,
                         username,
                         passphrase,
                         newPassphrase,
                         sslCertFile=None,
                         sslKeyFile=None,
                         sslKeyFilePassphrase=None):
        """change pass-phrase protecting the credentials for a given username

        @raise MyProxyClientGetError:
        @raise MyProxyClientRetrieveError:

        @param username: username of credential
        @param passphrase: existing pass-phrase for credential
        @param newPassphrase: new pass-phrase to replace the existing one.
        @param sslCertFile: certificate used for client authentication with
        the MyProxy server SSL connection.  This ID will be set as the owner
        of the stored credentials.  Only the owner can later remove
        credentials with myproxy-destroy or the destroy method.  If not set,
        this argument defaults to $GLOBUS_LOCATION/etc/hostcert.pem
        @param sslKeyFile: corresponding private key file.  See explanation
        for sslCertFile
        @param sslKeyFilePassphrase: passphrase for sslKeyFile.  Omit if the
        private key is not password protected.
        @return none
        """
        globusLoc = os.environ.get(MyProxyClient.GLOBUS_LOCATION_ENVVARNAME)
        if not sslCertFile or not sslKeyFile:
            if globusLoc:
                sslCertFile = os.path.join(globusLoc,
                                           *MyProxyClient.HOSTCERT_SUBDIRPATH)
                sslKeyFile = os.path.join(globusLoc,
                                          *MyProxyClient.HOSTKEY_SUBDIRPATH)
            else:
                raise MyProxyClientError(
            "No client authentication cert. and private key file were given")

        # Set-up SSL connection
        conn = self._initConnection(certFile=sslCertFile,
                                    keyFile=sslKeyFile,
                                    keyFilePassphrase=sslKeyFilePassphrase)

        conn.connect((self.hostname, self.port))

        # send globus compatibility stuff
        conn.write('0')

        # send command - ensure conversion from unicode before writing
        cmd = MyProxyClient.CHANGE_PASSPHRASE_CMD % (username,
                                                     passphrase,
                                                     newPassphrase)
        conn.write(str(cmd))

        # process server response
        dat = conn.recv(MyProxyClient.SERVER_RESP_BLK_SIZE)

        respCode, errorTxt = self._deserializeResponse(dat)
        if respCode:
            raise MyProxyClientGetError(errorTxt)

    def destroy(self,
                username,
                sslCertFile=None,
                sslKeyFile=None,
                sslKeyFilePassphrase=None):
        """destroy credentials from the server for a given username

        @raise MyProxyClientGetError:
        @raise MyProxyClientRetrieveError:

        @param username: username selected for credential
        @param sslCertFile: certificate used for client authentication with
        the MyProxy server SSL connection.  This ID will be set as the owner
        of the stored credentials.  Only the owner can later remove
        credentials with myproxy-destroy or the destroy method.  If not set,
        this argument defaults to $GLOBUS_LOCATION/etc/hostcert.pem
        @param sslKeyFile: corresponding private key file.  See explanation
        for sslCertFile
        @param sslKeyFilePassphrase: passphrase for sslKeyFile.  Omit if the
        private key is not password protected.
        @return none
        """
        globusLoc = os.environ.get(MyProxyClient.GLOBUS_LOCATION_ENVVARNAME)
        if not sslCertFile or not sslKeyFile:
            if globusLoc:
                sslCertFile = os.path.join(globusLoc,
                                         *MyProxyClient.HOSTCERT_SUBDIRPATH)
                sslKeyFile = os.path.join(globusLoc,
                                         *MyProxyClient.HOSTKEY_SUBDIRPATH)
            else:
                raise MyProxyClientError(
            "No client authentication cert. and private key file were given")

        # Set-up SSL connection
        conn = self._initConnection(certFile=sslCertFile,
                                    keyFile=sslKeyFile,
                                    keyFilePassphrase=sslKeyFilePassphrase)

        conn.connect((self.hostname, self.port))

        # send globus compatibility stuff
        conn.write('0')

        # send destroy command - ensure conversion from unicode before writing
        cmd = MyProxyClient.DESTROY_CMD % username
        conn.write(str(cmd))

        # process server response
        dat = conn.recv(MyProxyClient.SERVER_RESP_BLK_SIZE)

        respCode, errorTxt = self._deserializeResponse(dat)
        if respCode:
            raise MyProxyClientGetError(errorTxt)

    def store(self,
              username,
              passphrase,
              certFile,
              keyFile,
              sslCertFile=None,
              sslKeyFile=None,
              sslKeyFilePassphrase=None,
              lifetime=None,
              force=True):
        """Upload credentials to the server

        @raise MyProxyClientGetError:
        @raise MyProxyClientRetrieveError:

        @type username: string
        @param username: username selected for new credential
        @type passphrase: string
        @param passphrase: pass-phrase for new credential.  This is the pass
        phrase which protects keyfile.
        @type certFile: string
        @param certFile: user's X.509 certificate in PEM format
        @type keyFile: string
        @param keyFile: equivalent private key file in PEM format
        @type sslCertFile: string
        @param sslCertFile: certificate used for client authentication with
        the MyProxy server SSL connection.  This ID will be set as the owner
        of the stored credentials.  Only the owner can later remove
        credentials with myproxy-destroy or the destroy method.  If not set,
        this argument defaults to $GLOBUS_LOCATION/etc/hostcert.pem or if this
        is not set, certFile
        @type sslKeyFile: string
        @param sslKeyFile: corresponding private key file.  See explanation
        for sslCertFile
        @type sslKeyFilePassphrase: string
        @param sslKeyFilePassphrase: passphrase for sslKeyFile.  Omit if the
        private key is not password protected.  Nb. keyFile is expected to
        be passphrase protected as this will be the passphrase used for
        logon / getDelegation.
        @type Force: bool
        @param force: set to True to overwrite any existing creds with the
        same username.  If, force=False a check is made with a call to info.
        If creds already, exist exit without proceeding
        """

        lifetime = lifetime or self.proxyCertMaxLifetime

        # Inputs must be string type otherwise server will reject the request
        if isinstance(username, unicode):
            username = str(username)

        if isinstance(passphrase, unicode):
            passphrase = str(passphrase)

        globusLoc = os.environ.get(MyProxyClient.GLOBUS_LOCATION_ENVVARNAME)
        if not sslCertFile or not sslKeyFile:
            if globusLoc:
                sslCertFile = os.path.join(globusLoc,
                                           *MyProxyClient.HOSTCERT_SUBDIRPATH)
                sslKeyFile = os.path.join(globusLoc,
                                          *MyProxyClient.HOSTKEY_SUBDIRPATH)
            else:
                # Default so that the owner is the same as the ID of the
                # credentials to be uploaded.
                sslCertFile = certFile
                sslKeyFile = keyFile
                sslKeyFilePassphrase = passphrase

        if not force:
            # Check credentials don't already exist
            if self.info(username,
                         sslCertFile=sslCertFile,
                         sslKeyFile=sslKeyFile,
                         sslKeyFilePassphrase=sslKeyFilePassphrase)[0]:
                raise MyProxyCredentialsAlreadyExist(
                        "Credentials already exist for user: %s" % username)

        # Set up SSL connection
        conn = self._initConnection(certFile=sslCertFile,
                                    keyFile=sslKeyFile,
                                    keyFilePassphrase=sslKeyFilePassphrase)

        conn.connect((self.hostname, self.port))

        # send globus compatibility stuff
        conn.write('0')

        # send store command - ensure conversion from unicode before writing
        cmd = MyProxyClient.STORE_CMD % (username, lifetime)
        conn.write(str(cmd))

        # process server response
        dat = conn.recv(MyProxyClient.SERVER_RESP_BLK_SIZE)

        respCode, errorTxt = self._deserializeResponse(dat)
        if respCode:
            raise MyProxyClientGetError(errorTxt)

        # Send certificate and private key
        certTxt = open(certFile).read()
        keyTxt = open(keyFile).read()

        conn.send(certTxt + keyTxt)


        # process server response
        resp = conn.recv(MyProxyClient.SERVER_RESP_BLK_SIZE)
        respCode, errorTxt = self._deserializeResponse(resp)
        if respCode:
            raise MyProxyClientRetrieveError(errorTxt)

    def logon(self,
              username,
              passphrase,
              credname=None,
              lifetime=None,
              keyPair=None,
              certReq=None,
              nBitsForKey=PRIKEY_NBITS,
              bootstrap=False,
              updateTrustRoots=False,
              authnGetTrustRootsCall=False,
              sslCertFile=None,
              sslKeyFile=None,
              sslKeyFilePassphrase=None):
        """Retrieve a proxy credential from a MyProxy server

        Exceptions:  MyProxyClientGetError, MyProxyClientRetrieveError

        @type username: basestring
        @param username: username of credential

        @type passphrase: basestring
        @param passphrase: pass-phrase for private key of credential held on
        server

        @type credname: string / None type
        @param credname: optional credential name - provides additional means
        to specify credential to be retrieved

        @type lifetime: int
        @param lifetime: lifetime for generated certificate

        @type keyPair: OpenSSL.crypto.PKey
        @param keyPair: Public/Private key pair.  This is ignored if a
        certificate request is passed via the certReq keyword

        @type certReq: string
        @param certReq: ASN1 format certificate request, if none set, one is
        created along with a key pair

        @type nBitsForKey: int
        @param nBitsForKey: number of bits to use when generating key pair,
        defaults to the PRIKEY_NBITS class variable setting.  This keyword is
        ignored if a key pair is passed in from an external source via the
        keyPair keyword

        @rtype: tuple
        @return credentials as strings in PEM format: the
        user certificate, it's private key and the issuing certificate.  The
        issuing certificate is only set if the user certificate is a proxy

        @type bootstrap: bool
        @param bootstrap: If set to True, bootstrap trust roots i.e. connect to
        MyProxy server without verification of the server's SSL certificate
        against any CA certificates.  Set to False, for default behaviour:
        verify server SSL certificate against CA certificates held in location
        set by the "caCertDir" attribute.  If bootstrap is set, updateTrustRoots
        will be forced to True also

        @type updateTrustRoots: bool
        @param updateTrustRoots: set to True to update the trust roots

        @type authnGetTrustRootsCall: bool
        @param authnGetTrustRootsCall: pass username and password to
        getTrustRoots call.  getTrustRoots is invoked if the "updateTrustRoots"
        or "bootstrap" keywords are set.  This is not recommended for
        bootstrap since in this case the server is NOT authenticated by this
        client.

        @param sslCertFile: applies to SSL client based authentication -
        alternative to username/pass-phrase based.  This certificate is used for
        authentication with MyProxy server over the SSL connection.  If not set,
        this argument defaults to $GLOBUS_LOCATION/etc/hostcert.pem
        @param sslKeyFile: corresponding private key file.  See explanation
        for sslCertFile
        @param sslKeyFilePassphrase: passphrase for sslKeyFile.  Omit if the
        private key is not password protected.
        """
        if bootstrap:
            log.info('Bootstrapping MyProxy server root of trust.')

            # Bootstrap implies update to trust roots
            updateTrustRoots = True

        if updateTrustRoots:
            if authnGetTrustRootsCall:
                getTrustRootsKw = {
                    'username': username, 'passphrase': passphrase
                }
            else:
                getTrustRootsKw = {}

            self.getTrustRoots(writeToCACertDir=True,
                               bootstrap=bootstrap,
                               **getTrustRootsKw)

        lifetime = lifetime or self.proxyCertLifetime

        # Basic sanity check on username to avoid overhead on server
        if not username:
            raise MyProxyClientGetError('No username has been set')

        # Sanitise password - None is legal for modes where username/password
        # based authentication is not required
        if passphrase is None:
            passphrase = ''

        # Check for credential name setting
        if credname:
            if not isinstance(credname, basestring):
                raise TypeError('Expecting string type or None for "credname" '
                                'input argument')

            # Make a concatenated username credential parameter to pass
            userid = "%s-%s" % (username, credname)
        else:
            userid = username

        # Certificate request may be passed as an input but if not generate it
        # here
        if certReq is None:
            # If no key pair was passed, generate here
            if keyPair is None:
                keyPair = self._createKeyPair(nBitsForKey=nBitsForKey)

            certReq = self._createCertReq(username, keyPair)

        if keyPair is not None:
            pemKeyPair = crypto.dump_privatekey(crypto.FILETYPE_PEM, keyPair)


        # Check for certificate and private key set in environment which can
        # be used to authenticate with.  This is an alternative to the username
        # / passphrase based authentication
        if sslKeyFile is None or sslCertFile is None:
            sslKeyFile, sslCertFile = self.__class__.locateClientCredentials()

        # Set-up SSL connection
        conn = self._initConnection(certFile=sslCertFile,
                                    keyFile=sslKeyFile,
                                    keyFilePassphrase=sslKeyFilePassphrase)
        conn.connect((self.hostname, self.port))

        # send globus compatibility stuff
        conn.write('0')

        # send get command - ensure conversion from unicode before writing
        cmd = MyProxyClient.GET_CMD % (userid, passphrase, lifetime)

        conn.write(str(cmd))

        # process server response
        dat = conn.recv(MyProxyClient.SERVER_RESP_BLK_SIZE)

        respCode, errorTxt = self._deserializeResponse(dat)
        if respCode:
            raise MyProxyClientGetError(errorTxt)

        # Send certificate request
        conn.send(certReq)

        # process certificates
        # - 1st byte , number of certs
        dat = conn.recv(1)
        nCerts = ord(dat[0])

        # - n certs
        dat = conn.recv(MyProxyClient.SERVER_RESP_BLK_SIZE)

        # Check for error generating certificate
        try:
            respCode, errorTxt = self._deserializeResponse(dat)
            if respCode:
                raise MyProxyClientGetError(errorTxt)

        except ValueError:
            # If all is well, no error response will have been set so an attempt
            # to parse an error code will fail
            pass

        # process server response
        resp = conn.recv(MyProxyClient.SERVER_RESP_BLK_SIZE)
        respCode, errorTxt = self._deserializeResponse(resp)
        if respCode:
            raise MyProxyClientRetrieveError(errorTxt)

        # deserialize certs from received cert data
        pemCerts = self._deserializeCerts(dat)
        if len(pemCerts) != nCerts:
            MyProxyClientRetrieveError("%d certs expected, %d received" %
                                       (nCerts, len(pemCerts)))

        if keyPair is not None:
            # Return certs and private key
            # - proxy or dynamically issued certificate (MyProxy CA mode)
            # - private key
            # - rest of cert chain if proxy cert issued
            creds = [pemCerts[0], pemKeyPair]
            creds.extend(pemCerts[1:])
        else:
            # Key generated externally - return certificate chain only
            creds = pemCerts


        return tuple(creds)

    def getDelegation(self, *arg, **kw):
        """Retrieve proxy cert for user - same as logon"""
        return self.logon(*arg, **kw)

    def getTrustRoots(self,
                      username='',
                      passphrase='',
                      writeToCACertDir=False,
                      bootstrap=False):
        """Get trust roots for the given MyProxy server

        @type username: basestring
        @param username: username (optional)

        @type passphrase: basestring
        @param passphrase: pass-phrase (optional)
        server

        @type writeToCACertDir: bool
        @param writeToCACertDir: if set to True, write the retrieved trust roots
        out to the directory specified by the "caCertDir" attribute

        @type bootstrap: bool
        @param bootstrap: If set to True, bootstrap trust roots i.e. connect to
        MyProxy server without verification of the server's SSL certificate
        against any CA certificates.  Set to False, for default behaviour:
        verify server SSL certificate against CA certificates held in location
        set by the "caCertDir" attribute.

        @return: trust root files as a dictionary keyed by file name with each
        item value set to the file contents
        @rtype: dict
        """
        if bootstrap:
            log.info('Bootstrapping MyProxy server root of trust.')

        # Set-up SSL connection
        conn = self._initConnection(verifyPeerWithTrustRoots=(not bootstrap))
        conn.connect((self.hostname, self.port))

        # send globus compatibility stuff
        conn.write('0')

        # send get command - ensure conversion from unicode before writing
        cmd = MyProxyClient.GET_TRUST_ROOTS_CMD % (username, passphrase)
        conn.write(str(cmd))

        # process server response chunks until all consumed
        dat = ''
        tries = 0
        try:
            for tries in range(MyProxyClient.MAX_RECV_TRIES):
                dat += conn.recv(MyProxyClient.SERVER_RESP_BLK_SIZE)
        except SSL.SysCallError:
            # Expect this exception when response content exhausted
            pass

        # Precaution
        if tries == MyProxyClient.MAX_RECV_TRIES:
            log.warning('Maximum %d tries reached for getTrustRoots response '
                        'block retrieval with block size %d',
                        MyProxyClient.MAX_RECV_TRIES,
                        MyProxyClient.SERVER_RESP_BLK_SIZE)

        fieldName = MyProxyClient.TRUSTED_CERTS_FIELDNAME
        prefix = MyProxyClient.TRUSTED_CERTS_FILEDATA_FIELDNAME_PREFIX
        respCode, errorTxt, fileData = self._deserializeResponse(dat,
                                                                 fieldName,
                                                                 prefix)
        if respCode:
            raise MyProxyClientGetTrustRootsError(errorTxt)

        filesDict = dict([(k.split(prefix, 1)[1], base64.b64decode(v))
                          for k, v in fileData.items() if k != fieldName])

        if writeToCACertDir:
            # Create the CA directory path if doesn't already exist
            try:
                os.makedirs(self.caCertDir)
            except OSError, e:
                # Ignore if the path already exists
                if e.errno != errno.EEXIST:
                    raise

            for fileName, fileContents in filesDict.items():
                filePath = os.path.join(self.caCertDir, fileName)
                open(filePath, 'wb').write(fileContents)

        return filesDict
