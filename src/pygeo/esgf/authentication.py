import cherrypy
import os
from myproxy.client import MyProxyClient
from myproxy.client import MyProxyClientError
from urlparse import urlparse
import geocelery_conf
import socket
import utils

def authenticate(openid_uri, password):
    try:
        filepath = utils.user_url_to_filepath(openid_uri)
        host = urlparse(openid_uri.strip()).netloc;
        user = openid_uri.rsplit('/', 1)[1]
    except IndexError:
        raise MyProxyClientError('Invalid OpenID identifier')

    if not host or not user:
        raise MyProxyClientError('Invalid OpenID identifier')

    try:

        myproxy = MyProxyClient(hostname=host)
        credentials = myproxy.logon(user, password, bootstrap=True)
        cert_filepath = utils.user_cert_file(openid_uri)
        dir = os.path.dirname(cert_filepath);
        if not os.path.exists(dir):
            os.makedirs(dir)

        with open(cert_filepath, 'w') as fd:
            fd.write(credentials[0])
            fd.write(credentials[1])
    except socket.gaierror:
        raise MyProxyClientError('Invalid OpenID identifier')
