"""ESGF user authentication support for gaia."""

import getpass
import tempfile
import json
import socket
import os

import six
from six.moves import input

from gaia.esgf.proxy import MyProxyClient, MyProxyClientGetError


class OpenID(object):

    """An OpenID interface class for gaia.

    This class is responsible for handling and caching login
    credentials for OpenID accounts for ESGF.
    """

    #: The maximum number of times to attempt user interaction
    maxtries = 3

    def __init__(self,
                 host='pcmdi9.llnl.gov',
                 user=getpass.getuser(),
                 password=None,
                 interactive=False,
                 cache=None):
        """Construct the OpenID class instance.

        The user name and/or password are optional when calling this method
        with ``interactive = True``.  In this case, the user will be prompted
        to enter the credentials at the command line.  If a cache file is
        provided, credentials will be written to and read from this file.

        :param host: The user's OpenID host
        :type host: str
        :param user: The user's login name
        :type user: str
        :param password: The user's password
        :type password: str
        :param interactive: Ask for missing ID/password on the CLI
        :type interactive: bool
        :param cache: The path to a password cache file
        :type cache: str

        Examples:
        >>> id = OpenID()
        >>> id.login()     # non-interactive by default
        Traceback (most recent call last):
            ...
        MyProxyClientGetError: invalid password

        Interactively get input from the user.
        >>> id = OpenID(interactive=True)

        Provide user/password directly
        >>> id = OpenID(host='somehost.com', user='me', password='mysecret')

        or
        >>> id = OpenID()
        >>> id.user = 'me'
        >>> id.password = 'mysecret'
        >>> id.login() # doctest: +SKIP

        Cache the results in a file
        >>> id = OpenID(cache='esgf.json')
        >>> id.user = 'me'
        >>> id.password = 'mysecret'
        >>> id.login()  # doctest: +SKIP
        >>> id.credentials() # doctest: +SKIP
        """
        self.interactive = interactive
        self.host = host
        self.user = user
        self.password = password
        self.interactive = interactive

        # get cached information
        self._cache_file = cache
        if not cache:
            self._cache_stream = tempfile.NamedTemporaryFile(mode='w+')
            self._cache_stream.write('{}')
            self._cache_stream.flush()
            self._cache_file = self._cache_stream.name
        elif not os.path.exists(cache):
            try:
                os.makedirs(os.path.dirname(cache), mode=int('0700', 8))
            except OSError:
                pass
            open(cache, 'w').write('{}')
            try:
                os.chmod(self._cache_file, int('0600', 8))
            except Exception:
                pass

        s = open(self._cache_file, 'r').read()

        try:
            self._cache = json.loads(s)
        except ValueError:
            self._cache = {}

    @classmethod
    def _format_prompt(cls, prompt, default=None):
        """Format a string as a prompt for input."""
        if isinstance(default, six.string_types) and default:
            return '{0} [{1}]: '.format(prompt, default)
        else:
            return prompt + ': '

    @classmethod
    def _prompt(cls, text, default=None, hide=False):
        """Generate a prompt for user input and return the result."""
        hdefault = default
        p = input
        if hide:
            hdefault = '*' * 8
            p = getpass.getpass
        return p(cls._format_prompt(text, hdefault)) or default

    def interact(self):
        """Interact with the user to input login information."""
        if not self.interactive:
            raise Exception('Non-interactive session')

        self.host = self._prompt('Enter your ESGF authentication host', self.host)
        self.user = self._prompt('Enter your ESGF user name', self.user)
        self.password = self._prompt('Enter your ESGF password', self.password, True)

    def _write_cache(self):
        """Write in memory cache to disk."""
        open(self._cache_file, 'w').write(
            json.dumps(self._cache)
        )

    def login(self, proxyargs={}, logonargs={}):
        """Login to the ESGF server and cache/return the credentials.

        :param proxyargs: Keyword argmuents given to the MyProxyConfig constructor.
        :type proxyargs: dict
        :param logonargs: Keyword arguments given to the MyProxyConfig logon.
        :type proxyargs: dict
        :returns: Log in credentials
        :rtype: tuple
        """
        self._certs = None

        i = 0
        while True:
            client = MyProxyClient(hostname=self.host)
            try:
                certs = client.logon(
                    self.user,
                    self.password
                )
                self._cache[self.host] = {
                    self.user: certs
                }
                self._write_cache()
            except (MyProxyClientGetError, socket.gaierror):
                if not self.interactive or i >= self.maxtries:
                    raise
                if i:
                    print('Could not log in with provided credentials.')
                self.interact()
                i += 1
                continue
            break
        return certs

    def invalidate(self, allusers=False, allhosts=False):
        """Invalidate the cached certificates.

        :param allusers: Invalidate the cache for all users
        :param allhosts: Invalidate the cache for all hosts
        """
        if allhosts:
            self._cache = {}
        else:
            h = self._cache.get(self.host)
            if h:
                if allusers:
                    h = {}
                elif h.get(self.user):
                    del h[self.user]
        self._write_cache()

    def credentials(self):
        """Return the logon credentials for the current ESGF server.

        This will log in to refresh the connection as necessary.

        :returns: (proxy or dynamic cert, private key, cert chain)
        :rtype: tuple
        """
        certs = self._cache.get(self.host, {}).get(self.user, {})

        if not certs:
            certs = self.login()

        return certs

if __name__ == '__main__':

    # force reload the credentials
    cache = os.path.join(
        os.path.expanduser('~'),
        '.gaia',
        'esgf.auth.json'
    )
    id = OpenID(interactive=True, cache=cache)
    print('\n'.join(id.login()))
