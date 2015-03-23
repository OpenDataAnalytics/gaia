"""Test logging into an ESGF server with mocked MyProxy methods."""

import socket
import tempfile
import json
import sys
import warnings

from mock import patch

from base import TestCase
from gaia import esgf
from gaia.esgf.proxy import MyProxyClientGetError

warnings.simplefilter('ignore', DeprecationWarning)


def validate(*arg, **kw):
    """Validate an esgf logon."""
    if arg[0].hostname != 'esgf-node':
        raise socket.gaierror()
    elif arg[1] != 'auser':
        raise MyProxyClientGetError('invalid username')
    elif arg[2] != 'apassword':
        raise MyProxyClientGetError('invalid password')
    elif len(arg) != 3:
        raise Exception('unknown call')

    return 'secret'


class AuthTest(TestCase):

    """Test esgf authorization."""

    def mock(self):
        """Mock the MyProxyClient logon method."""
        return patch.object(
            esgf.proxy.MyProxyClient,
            'logon',
            side_effect=validate, autospec=True
        )

    def test_invalid_host(self):
        """Test logging in with a known bad host."""
        with self.mock() as logon:

            id = esgf.auth.OpenID(host='not a valid host')
            id.user = 'auser'
            id.password = 'apassword'

            try:
                id.login()
            except socket.gaierror:
                pass

            self.assertEqual(logon.call_count, 1)

    def test_invalid_user(self):
        """Test logging in with a known bad username."""
        with self.mock() as logon:

            id = esgf.auth.OpenID(host='esgf-node')
            id.user = 'notauser'
            id.password = 'apassword'

            try:
                id.login()
            except MyProxyClientGetError as e:
                if str(e) != 'invalid username':
                    raise

            self.assertEqual(logon.call_count, 1)

    def test_invalid_password(self):
        """Test logging in with a known bad username."""
        with self.mock() as logon:

            id = esgf.auth.OpenID(host='esgf-node')
            id.user = 'auser'
            id.password = 'notapassword'

            try:
                id.login()
            except MyProxyClientGetError as e:
                if str(e) != 'invalid password':
                    raise

            self.assertEqual(logon.call_count, 1)

    def test_valid_login(self):
        """Test logging in with valid credentials."""
        with self.mock() as logon:

            id = esgf.auth.OpenID(host='esgf-node')
            id.user = 'auser'
            id.password = 'apassword'

            self.assertEqual(id.login(), 'secret')
            self.assertEqual(logon.call_count, 1)

        with self.mock() as logon:

            id = esgf.auth.OpenID(host='esgf-node', user='auser')
            id.password = 'apassword'

            self.assertEqual(id.login(), 'secret')
            self.assertEqual(logon.call_count, 1)

        with self.mock() as logon:

            id = esgf.auth.OpenID(host='esgf-node', user='auser', password='apassword')

            self.assertEqual(id.login(), 'secret')
            self.assertEqual(logon.call_count, 1)

    def test_login_caching(self):
        """Test login caching."""
        with self.mock() as logon:

            id = esgf.auth.OpenID(host='esgf-node', user='auser', password='apassword')

            self.assertEqual(id.login(), 'secret')
            self.assertEqual(id.login(), 'secret')
            self.assertEqual(logon.call_count, 2, 'login should not cache')

        with self.mock() as logon:

            id = esgf.auth.OpenID(host='esgf-node', user='auser', password='apassword')

            self.assertEqual(id.credentials(), 'secret')
            self.assertEqual(id.credentials(), 'secret')
            self.assertEqual(logon.call_count, 1, 'credentials should cache')

    def test_login_session_caching(self):
        """Test caching with a given cache file."""
        tmp = tempfile.NamedTemporaryFile(mode='w+')

        with self.mock() as logon:

            id = esgf.auth.OpenID(
                host='esgf-node',
                user='auser',
                password='apassword',
                cache=tmp.name
            )

            self.assertEqual(id.credentials(), 'secret')
            self.assertEqual(logon.call_count, 1, 'first login')

            id = esgf.auth.OpenID(
                host='esgf-node',
                user='auser',
                password='apassword',
                cache=tmp.name
            )

            self.assertEqual(id.credentials(), 'secret')
            self.assertEqual(logon.call_count, 1,
                             'logon in second session should be cached')

    def test_session_invalidate_all(self):
        """Test invalidating a cache."""
        tmp = tempfile.NamedTemporaryFile(mode='w+')
        tmp.write(
            '{"host1": {"user1": "password1"}, "esgf-node": {"buser": "bpassword"}}'
        )
        tmp.flush()

        with self.mock() as logon:

            id = esgf.auth.OpenID(
                host='esgf-node',
                user='auser',
                password='apassword',
                cache=tmp.name
            )

            self.assertEqual(id.credentials(), 'secret')

            id.invalidate(allhosts=True)
            self.assertEqual(logon.call_count, 1, 'first login')

            tmp.flush()
            tmp.seek(0)
            self.assertEqual(tmp.read(), '{}', 'cache file should be empty')

            id = esgf.auth.OpenID(
                host='esgf-node',
                user='auser',
                password='apassword',
                cache=tmp.name
            )

            self.assertEqual(id.credentials(), 'secret')
            self.assertEqual(logon.call_count, 2,
                             'logon in second session should not be cached')

    def test_session_invalidate(self):
        """Test invalidating a cache."""
        tmp = tempfile.NamedTemporaryFile(mode='w+')
        tmp.write(
            '{"host1": {"user1": "password1"}, "esgf-node": {"buser": "bpassword"}}'
        )
        tmp.flush()

        with self.mock() as logon:

            id = esgf.auth.OpenID(
                host='esgf-node',
                user='auser',
                password='apassword',
                cache=tmp.name
            )

            self.assertEqual(id.credentials(), 'secret')

            id.invalidate()
            self.assertEqual(logon.call_count, 1, 'first login')

            tmp.seek(0)
            cache = json.loads(tmp.read())
            self.assertEqual(cache['host1']['user1'], 'password1',
                             'cache file should have original host')

            self.assertTrue('esgf-node' not in cache,
                            'cache file should not have the current host')

            id = esgf.auth.OpenID(
                host='esgf-node',
                user='auser',
                password='apassword',
                cache=tmp.name
            )

            self.assertEqual(id.credentials(), 'secret')
            self.assertEqual(logon.call_count, 2,
                             'logon in second session should not be cached')

    @patch('gaia.esgf.auth.input')
    @patch('gaia.esgf.auth.getpass.getpass')
    def test_interactive_maxtries(self, mock_getpass, mock_input):
        """Test setting user/password from an interactive prompt with maxtries."""
        _out = sys.stdout
        sys.stdout = tempfile.TemporaryFile(mode='w+')
        mock_input.return_value = 'invalid'
        mock_getpass.return_value = 'invalid'
        with self.mock() as login:

            id = esgf.auth.OpenID(interactive=True)
            id.host = 'defaulthost'
            id.user = 'defaultuser'
            id.password = 'defaultpassword'

            try:
                id.login()
            except Exception:
                pass

            self.assertEqual(login.call_count, id.maxtries + 1)
        sys.stdout.close()
        sys.stdout = _out

    @patch('gaia.esgf.auth.input')
    @patch('gaia.esgf.auth.getpass.getpass')
    def test_interactive_1try(self, mock_pass, mock_input):
        """Test setting user/password from an interactive prompt with maxtries."""
        _out = sys.stdout
        sys.stdout = tempfile.TemporaryFile(mode='w+')

        def input_response(prompt, *arg, **kw):
            if prompt.find('authentication host') >= 0:
                return 'esgf-node'
            if input_response.called:
                return 'auser'
            else:
                input_response.called = True
                return 'invalid'

        input_response.called = False
        mock_input.side_effect = input_response
        mock_pass.return_value = 'apassword'
        with self.mock() as login:

            id = esgf.auth.OpenID(interactive=True)
            id.host = 'defaulthost'
            id.user = 'defaultuser'
            id.password = 'defaultpassword'

            try:
                id.login()
            except Exception:
                pass

            self.assertEqual(login.call_count, 3)
        sys.stdout.close()
        sys.stdout = _out
