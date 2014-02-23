"""
Lightweight command-line interface to MyProxyClient.

Sub commands
------------

``myproxyclient logon`` a replacement for myproxy-logon.  It understands most of
the same options and tries to behave the same with a few exceptions:

  1. -C/--cadir allows you to override the CA directory
  2. It will not write the credentials to /tmp.  You must either set
     X509_USER_PROXY or specify the ``-o`` option.

"""

__author__ = "Stephen Pascoe"
__date__ = "17/06/2010"
__copyright__ = "(C) 2010 Science and Technology Facilities Council"
__license__ = __license__ = """BSD - See LICENSE file in top-level directory

For myproxy_logon see Access Grid Toolkit Public License (AGTPL)

This product includes software developed by and/or derived from the Access
Grid Project (http://www.accessgrid.org) to which the U.S. Government retains
certain rights."""

__revision__ = '$Id: script.py 7928 2011-08-12 13:16:26Z pjkersha $'

import sys
import optparse
import getpass
import os

from myproxy.client import MyProxyClient


def make_optparser():
    """Make command line option parser

    @rtype: optparse.OptionParser
    @return: option parser instance
    """
    usage = """\
usage: %prog [command] [options]

commands:
  logon        Retrieve credentials from a MyProxy service
"""

    op = optparse.OptionParser(usage=usage)

    op.add_option('-o', '--out', dest='outfile',
                  action='store', type='string',
                  help='''\
Set the file to store the retrieved credentials.
If not specified credentials will be stored in X509_USER_PROXY environment
variable.  To write the credential to stdout use -o -.
''')

    op.add_option('-C', '--cadir', dest='cadir',
                  action='store', type='string',
                  help='''\
Set location of trusted certificates.  By default this is the X509_CERT_DIR
environment variable or ~/.globus/certificates or /etc/grid-security.
''')

    op.add_option('-s', '--pshost', dest='hostname',
                  action='store', type='string',
                  help='Set hostname of myproxy server')

    op.add_option('-p', '--psport', dest='port',
                  action='store', type='int',
                  help='Set port of myproxy server')

    op.add_option('-n', '--no_passphrase', dest='no_pass',
                  action='store_true',
                  help='Don\'t prompt for pass-phrase')

    op.add_option('-k', '--credname', dest='credname',
                  action='store', type='string',
                  help='Specify credential name')

    def set_lifetime(opt, opt_str, val, op):
        """Callback to convert input requested proxy lifetime from hours to
        seconds

        @type opt: optparse.Option
        @param opt: Option instance that is calling the callback
        @type opt_str: string
        @param opt_str: option string seen on the command-line that's triggering
        this callback
        @type val: float
        @param val: argument to this option seen on the command-line
        @type op: optparse.OptionParser
        @param op: OptionParser instance
        """
        op.values.lifetime = int(val * 60 * 60)

    op.add_option('-t', '--proxy_lifetime', type='int',
                  action='callback', callback=set_lifetime,
                  help='Set proxy certificate Lifetime (hours)')

    op.add_option('-S', '--stdin_pass', dest='stdin_pass',
                  action='store_true',
                  help='Read the password directly from stdin')

    op.add_option('-b', '--bootstrap', dest='bootstrap',
                  action='store_true',
                  help='Bootstrap trust in MyProxy server downloading trusted '
                       'CA certificates')

    op.add_option('-T', '--trustroots', dest='trustroots',
                  action='store_true',
                  help='Update trustroots')

    op.add_option('-l', '--username', dest='username',
                  action='store', type='string',
                  help=\
        'Set username.  Defaults to "LOGNAME" environment variable setting.')

    op.set_defaults(
        outfile=None,
        cadir=MyProxyClient.PROPERTY_DEFAULTS['caCertDir'],
        hostname=MyProxyClient.PROPERTY_DEFAULTS['hostname'],
        port=MyProxyClient.PROPERTY_DEFAULTS['port'],
        lifetime=MyProxyClient.PROPERTY_DEFAULTS['proxyCertLifetime'],
        bootstrap=False,
        trustroots=False,
        openid=None,
        username=None,
        stdin_pass=False,
        no_pass=False,
        )

    return op


def main(argv=sys.argv):
    op = make_optparser()

    logname = os.environ.get('LOGNAME')

    nArgs = len(argv)
    if nArgs < 2:
        op.error('No command set')
    else:
        command = argv[1]

    # Catch example of just specifying --help or '-h'
    if command in ['--help', '-h']:
        argl = argv[1:2]
        command = None

    elif command != 'logon':
        op.error('Command %s not supported' % command)

    elif nArgs < 3:
        op.error('No command options set')

    else:
        argl = argv[2:]

    options = op.parse_args(argl)[0]

    if options.outfile is None:
        if MyProxyClient.X509_USER_PROXY_ENVVARNAME in os.environ:
            options.outfile = os.environ[
                                    MyProxyClient.X509_USER_PROXY_ENVVARNAME]
        else:
            op.error("Credential output file must be specified or %r set" %
                     MyProxyClient.X509_USER_PROXY_ENVVARNAME)

    if options.username is None:
        options.username = logname

    if options.cadir:
        cadir = options.cadir

    elif MyProxyClient.X509_CERT_DIR_ENVVARNAME in os.environ:
        cadir = os.environ[MyProxyClient.X509_CERT_DIR_ENVVARNAME]

    elif logname == 'root':
        cadir = MyProxyClient.ROOT_TRUSTROOT_DIR
    else:
        cadir = os.path.join(
                        os.path.expanduser(MyProxyClient.USER_TRUSTROOT_DIR))

    client_props = dict(caCertDir=cadir,
                        hostname=options.hostname,
                        port=options.port,
                        proxyCertLifetime=options.lifetime,
                        )

    myproxy = MyProxyClient(**client_props)

    do_logon(myproxy, options)


def do_logon(myproxy, options):
    """Execute MyProxy logon command

    @type myproxy: myproxy.client.MyProxyClient
    @param myproxy: MyProxy client object
    @type options:
    @param options: command line options
    """
    if options.stdin_pass:
        #!TODO: Is this right to read just the first line of stdin?
        password = sys.stdin.readline().rstrip()
    elif options.no_pass:
        password = None
    else:
        password = getpass.getpass('Enter password for user %r on MyProxy '
                                   'server %r:'
                                   % (options.username, options.hostname))

    creds = myproxy.logon(options.username, password,
                          credname=options.credname,
                          bootstrap=options.bootstrap,
                          updateTrustRoots=options.trustroots)

    if options.outfile == '-':
        fout = sys.stdout
    else:
        fout = open(options.outfile, 'w')

    for cred in creds:
        fout.write(cred)

    if fout != sys.stdout:
        fout.close()


if __name__ == '__main__':
    main()
