import cherrypy
from cherrypy.lib import cptools
from mako.template import Template
from mako.lookup import TemplateLookup
import pymongo
import os
import esgf.authentication
import traceback
from urlparse import urlparse

from myproxy.client import MyProxyClientError

current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, "../")
lookup = TemplateLookup(directories=[template_dir])

class ESGFSessionAuth(cptools.SessionAuth):

    def check_username_and_password(self, username, password):
        try:
            esgf.authentication.authenticate(username, password)
        except MyProxyClientError as myex:
            return "ESGF authentication error: %s" % myex.message
        except Exception as ex:
            return "Internal server error: %s" % str(ex)

    def login_screen(self, from_page='..', username='', error_msg=''):
        template = lookup.get_template("login.html")
        return template.render(from_page=from_page,
                               username=username,
                               error_message=error_msg);

    def runtool(cls, **kwargs):
        sa = cls()
        for k, v in kwargs.iteritems():
            setattr(sa, k, v)
        return sa.run()

    runtool = classmethod(runtool)

    def do_check(self):
          request = cherrypy.serving.request

          if request.path_info.startswith('/common/') or request.path_info == '/favicon.ico':
              return True
          else:
              return super(ESGFSessionAuth, self).do_check()

    def on_login(self, username):
        username = username.strip()
        host = cherrypy.config['mongo.host']
        db = cherrypy.config['mongo.db']
        c = pymongo.Connection(host)[db]['users']

        if c.find({'openIdUri': username}).count() == 0:
            c.insert({'openIdUri': username})

        # Save base url in session for easy access
        parse_result = urlparse(username)
        esgf_base_url = '%s://%s' % (parse_result.scheme, parse_result.netloc)
        cherrypy.session['ESGFBaseUrl'] = esgf_base_url

cherrypy.tools.esgf_session_auth = cherrypy._cptools.HandlerTool(ESGFSessionAuth.runtool)
