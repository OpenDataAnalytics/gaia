from celery import Celery
from celery import task, current_task
from celery.result import AsyncResult
import requests
import cherrypy
from bs4 import BeautifulSoup

from pygeo.esgf.utils import user_cert_file

mongo_url='mongodb://localhost/celery'
celery = Celery('download', broker=mongo_url, backend=mongo_url)

def register_groups(taskId):
    task = AsyncResult(taskId, backend=celery.backend)
    soup = BeautifulSoup(task.result)

    attributes = ['group', 'role', 'url']
    groups = []

    for form in soup.find_all('form'):
        details = {}
        for input in form.find_all('input'):
            name = input.get('name')
            value = input.get('value')

            if name and value and name in attributes:
                details[name] =  value

        groups.append(details)

    return groups

def register_with_group(url, group, role):
    url = url.strip('"')
    user_url = cherrypy.session['username']
    cert_filepath = user_cert_file(user_url)

    xml = '<esgf:form xmlns:esgf=\"http://www.esgf.org/\">'\
    '<esgf:group>%s</esgf:group>'\
    '<esgf:role>%s</esgf:role>'\
    '<esgf:user>%s</esgf:user>'\
    '</esgf:form>'

    post_data = {'xml': xml % (group if group else "",
                               role if role else "", user_url)}

    r = requests.post(url, data=post_data,
                      cert=(cert_filepath, cert_filepath), verify=False)

    result = True

    if r.status_code != 200:
        cherrypy.log('Error registering with ESGF: %d' % r.status_code)
        cherrypy.log(r.text)
        result = False

    return result
