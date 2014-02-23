#!/usr/bin/env python
"""MyProxy Client unit tests

NERC Data Grid Project
"""
__author__ = "P J Kershaw"
__date__ = "02/07/07"
__copyright__ = "(C) 2009 Science and Technology Facilities Council"
__license__ = """BSD- See LICENSE file in top-level directory"""
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__revision__ = '$Id: test_myproxyclient.py 7936 2011-10-11 13:47:07Z pjkersha $'
import logging
logging.basicConfig(level=logging.DEBUG)

import unittest
import os
from getpass import getpass
from os import path

from OpenSSL import crypto

from myproxy.client import CaseSensitiveConfigParser, MyProxyClient

mkPath = lambda file: path.join(os.environ['MYPROXYCLIENT_UNITTEST_DIR'], file)

class _MyProxyClientTestCase(unittest.TestCase):
    '''Base implements environment settings common to all test case classes'''
    if 'NDGSEC_INT_DEBUG' in os.environ:
        import pdb
        pdb.set_trace()

    if 'MYPROXYCLIENT_UNITTEST_DIR' not in os.environ:
        os.environ['MYPROXYCLIENT_UNITTEST_DIR'] = \
                                        path.abspath(path.dirname(__file__))


class MyProxyClientLiveTestCase(_MyProxyClientTestCase):
    '''Tests require a connection to a real MyProxy service running on a host.

    The server must be set up as a credential repository - i.e. able to receive
    and store credentials
    '''
    CONFIG_FILENAME = "myProxyClientTest.cfg"


    def setUp(self):

        super(MyProxyClientLiveTestCase, self).setUp()

        configParser = CaseSensitiveConfigParser()
        configFilePath = path.join(os.environ['MYPROXYCLIENT_UNITTEST_DIR'],
                                   MyProxyClientLiveTestCase.CONFIG_FILENAME)
        configParser.read(configFilePath)

        self.cfg = {}
        for section in configParser.sections():
            self.cfg[section] = dict(configParser.items(section))

        configFilePath = path.expandvars(self.cfg['setUp']['cfgFilePath'])
        self.clnt = MyProxyClient(cfgFilePath=configFilePath)

        # Get trust roots bootstrapping trust ready for test
        self.trustRoots = self.clnt.getTrustRoots(writeToCACertDir=True,
                                                  bootstrap=True)

        # Keep a copy of files stored ready for tearDown tidy up
        self.trustRootFiles = []

        dirContents = os.listdir(self.clnt.caCertDir)
        for fileName in self.trustRoots:
            self.assert_(fileName in dirContents)
            file_path = os.path.join(self.clnt.caCertDir, fileName)
            self.trustRootFiles.append(file_path)

    def tearDown(self):
        """Clear up CA certs retrieved in test01GetTrustRoots call ready for
        next run of these unit tests
        """
        self.trustRoots = None
        self._deleteTrustRootFiles()

    def _deleteTrustRootFiles(self):
        """Helper method clears up CA certs in trust roots directory set from
        previous call to test01GetTrustRoots()
        """
        for fileName in self.trustRootFiles:
            os.remove(fileName)

    def test01GetTrustRoots(self):
        # Test output from getTrustRoots call made in setUp
        self.assert_(self.trustRoots)
        self.assert_(isinstance(self.trustRoots, dict))
        self.assert_(len(self.trustRoots) > 0)
        for fileName, fileContents in self.trustRoots.items():
            if fileName.endswith('.0'):
                # test parsing certificate
                cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                               fileContents)
                self.assert_(cert)
                self.assert_(isinstance(cert, crypto.X509))
                subj = cert.get_subject()
                self.assert_(subj)
                print("Trust root certificate retrieved with DN=%s" % subj)

    def test02Store(self):
        # Test get trust root to bootstrap trust
        self.test01GetTrustRoots()

        # upload X509 cert and private key to repository
        thisSection = self.cfg['test02Store']

        passphrase = thisSection.get('passphrase')
        if passphrase is None:
            passphrase = getpass("\ntest02Store credential pass-phrase: ")

        sslKeyFilePassphrase = thisSection.get('sslKeyFilePassphrase')
        if sslKeyFilePassphrase is None:
            sslKeyFilePassphrase = getpass("\ntest02Store credential owner "
                                           "pass-phrase: ")

        certFile = path.expandvars(thisSection['ownerCertFile'])
        keyFile = path.expandvars(thisSection['ownerKeyFile'])
        sslCertFile = path.expandvars(thisSection['sslCertFile'])
        sslKeyFile = path.expandvars(thisSection['sslKeyFile'])

        self.clnt.store(thisSection['username'],
                        passphrase,
                        certFile,
                        keyFile,
                        sslCertFile=sslCertFile,
                        sslKeyFile=sslKeyFile,
                        sslKeyFilePassphrase=sslKeyFilePassphrase,
                        force=False)
        print("Store creds for user %s" % thisSection['username'])

    def test03GetDelegation(self):
        # retrieve proxy cert./private key
        thisSection = self.cfg['test03GetDelegation']

        passphrase = thisSection.get('passphrase')
        if passphrase is None:
            passphrase = getpass("\ntest03GetDelegation passphrase: ")

        proxyCertFile = path.expandvars(thisSection['proxyCertFileOut'])
        proxyKeyFile = path.expandvars(thisSection['proxyKeyFileOut'])

        creds = self.clnt.getDelegation(thisSection['username'], passphrase)
        print "proxy credentials:"
        print ''.join(creds)
        open(proxyCertFile, 'w').write(creds[0]+''.join(creds[2:]))
        open(proxyKeyFile, 'w').write(creds[1])

    def test04Info(self):
        # Retrieve information about a given credential
        thisSection = self.cfg['test04Info']

        # sslKeyFilePassphrase can be omitted from the congif file in which case
        # the get call below would return None
        sslKeyFilePassphrase = thisSection.get('sslKeyFilePassphrase')
        if sslKeyFilePassphrase is None:
            sslKeyFilePassphrase = getpass("\ntest04Info owner credentials "
                                           "passphrase: ")

        credExists, errorTxt, fields = self.clnt.info(
                                 thisSection['username'],
                                 path.expandvars(thisSection['sslCertFile']),
                                 path.expandvars(thisSection['sslKeyFile']),
                                 sslKeyFilePassphrase=sslKeyFilePassphrase)
        print "test04Info... "
        print "credExists: %s" % credExists
        print "errorTxt: " + errorTxt
        print "fields: %s" % fields

    def test06ChangePassphrase(self):
        # change pass-phrase protecting a given credential
        thisSection = self.cfg['test06ChangePassphrase']

        passphrase = thisSection.get('passphrase')
        if passphrase is None:
            passphrase = getpass("test06ChangePassphrase - passphrase: ")

        newPassphrase = thisSection.get('newPassphrase')
        if newPassphrase is None:
            newPassphrase = getpass("test06ChangePassphrase - new passphrase: ")

            confirmNewPassphrase = getpass("test06ChangePassphrase - confirm "
                                           "new passphrase: ")

            if newPassphrase != confirmNewPassphrase:
                self.fail("New and confirmed new password don't match")

        sslKeyFilePassphrase = thisSection.get('sslKeyFilePassphrase') or \
                            passphrase

        self.clnt.changePassphrase(thisSection['username'],
                               passphrase,
                               newPassphrase,
                               path.expandvars(thisSection['sslCertFile']),
                               path.expandvars(thisSection['sslKeyFile']),
                               sslKeyFilePassphrase=sslKeyFilePassphrase)
        print("Changed pass-phrase")

    def test05GetDelegationWithBootstrappedTrustRoots(self):
        # Get delegation call whilst simulataneously bootstrapping trust roots
        thisSection = self.cfg['test05GetDelegationWithBootstrappedTrustRoots']

        passphrase = thisSection.get('passphrase')
        if passphrase is None:
            passphrase = getpass("\n"
                                 "test05GetDelegationWithBootstrappedTrustRoots"
                                 "passphrase: ")

        # Ensure any previously set trust root files are removed
        self._deleteTrustRootFiles()

        creds = self.clnt.getDelegation(thisSection['username'], passphrase,
                                        bootstrap=True)
        print "proxy credentials:"
        print ''.join(creds)

    def test07Destroy(self):
        # destroy credentials for a given user
        thisSection = self.cfg['test07Destroy']

        sslKeyFilePassphrase = thisSection.get('sslKeyFilePassphrase')
        if sslKeyFilePassphrase is None:
            sslKeyFilePassphrase = getpass("\ntest07Destroy credential owner "
                                           "passphrase: ")

        self.clnt.destroy(thisSection['username'],
                      sslCertFile=path.expandvars(thisSection['sslCertFile']),
                      sslKeyFile=path.expandvars(thisSection['sslKeyFile']),
                      sslKeyFilePassphrase=sslKeyFilePassphrase)
        print("Destroy creds for user %s" % thisSection['username'])


from myproxy.utils.openssl import OpenSSLConfigError

class MyProxyClientInterfaceTestCase(_MyProxyClientTestCase):
    '''Test interface for correct getting/setting of attributes'''
    HOSTCERT_FILENAME = 'localhost.crt'
    HOSTCERT_FILEPATH = mkPath(HOSTCERT_FILENAME)
    HOSTCERT_DN = '/O=NDG/OU=Security/CN=localhost'

    def test01EnvironmentVarsSet(self):

        try:
            environBackup = os.environ.copy()

            os.environ['MYPROXY_SERVER'] = 'localhost.domain'
            os.environ['MYPROXY_SERVER_DN'] = '/O=NDG/OU=Raphael/CN=raphael'
            os.environ['MYPROXY_SERVER_PORT'] = '20000'
            client = MyProxyClient(openSSLConfFilePath=mkPath('openssl.conf'),
                                   proxyCertMaxLifetime=60000,
                                   proxyCertLifetime=30000,
                                   caCertDir=mkPath(''))

            self.assert_(client.port == 20000)
            self.assert_(client.hostname == 'localhost.domain')
            self.assert_(client.serverDN == '/O=NDG/OU=Raphael/CN=raphael')
            self.assert_(client.proxyCertMaxLifetime == 60000)
            self.assert_(client.proxyCertLifetime == 30000)
            self.assert_(client.openSSLConfFilePath == mkPath('openssl.conf'))
            self.assert_(client.caCertDir == mkPath(''))
        finally:
            os.environ = environBackup

    def test02SetProperties(self):

        client = MyProxyClient()
        try:
            client.port = None
            self.fail("Expecting AttributeError raised from port set to "
                      "invalid type")
        except TypeError:
            pass

        client.port = 8000
        client.hostname = '127.0.0.1'
        client.serverDN = '/O=NDG/OU=BADC/CN=raphael'
        client.proxyCertMaxLifetime = 80000
        client.proxyCertLifetime = 70000

        try:
            client.openSSLConfFilePath = mkPath('ssl.cnf')
            self.fail("Expecting OpenSSLConfigError raised for invalid file "
                      "'ssl.cnf'")
        except OpenSSLConfigError:
            pass

        client.caCertDir = mkPath('/etc/grid-security/certificates')

        self.assert_(client.port == 8000)
        self.assert_(client.hostname == '127.0.0.1')
        self.assert_(client.serverDN == '/O=NDG/OU=BADC/CN=raphael')
        self.assert_(client.proxyCertMaxLifetime == 80000)
        self.assert_(client.proxyCertLifetime == 70000)
        self.assert_(client.openSSLConfFilePath == mkPath('ssl.cnf'))
        self.assert_(
                client.caCertDir == mkPath('/etc/grid-security/certificates'))

    def test03SSLVerification(self):
        # SSL verification callback

        # Ensure no relevant environment variables are set which might affect
        # the result
        try:
            serverDN = os.environ.get(
                                    MyProxyClient.MYPROXY_SERVER_DN_ENVVARNAME)
            if serverDN is not None:
                del os.environ[MyProxyClient.MYPROXY_SERVER_DN_ENVVARNAME]

            serverName = os.environ.get(MyProxyClient.MYPROXY_SERVER_ENVVARNAME)
            if serverName is not None:
                del os.environ[MyProxyClient.MYPROXY_SERVER_ENVVARNAME]

            client = MyProxyClient()

            connection = None
            errorStatus = False
            successStatus = True
            errorDepth = 0
            peerCertStr = open(self.__class__.HOSTCERT_FILEPATH).read()
            peerCert = crypto.load_certificate(crypto.FILETYPE_PEM, peerCertStr)

            args = (connection, peerCert, errorStatus, errorDepth,
                    successStatus)

            # This would normally called implicitly during the SSL handshake
            status = client.serverSSLCertVerify(*args)
            self.assert_(status == successStatus)

            # Match based on full DN instead - this takes precedence over
            # hostname match
            client.serverDN = self.__class__.HOSTCERT_DN
            status = client.serverSSLCertVerify(*args)
            self.assert_(status == successStatus)

        finally:
            if serverDN is not None:
                os.environ[MyProxyClient.MYPROXY_SERVER_DN_ENVVARNAME
                           ] = serverDN

            if serverName is not None:
                os.environ[MyProxyClient.MYPROXY_SERVER_ENVVARNAME
                           ] = serverName


if __name__ == "__main__":
    unittest.main()
