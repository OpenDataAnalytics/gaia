from celery import Celery
from celery import task, current_task
from celery.result import AsyncResult
from celery.exceptions import SoftTimeLimitExceeded
import requests
import os.path
from functools import partial
import hashlib
from urlparse import urlparse
import cherrypy
import utils

mongo_url='mongodb://localhost/celery'
celery = Celery('download', broker=mongo_url, backend=mongo_url)

@celery.task
def download(url, size, checksum, user_url):
    url = url.strip('"')
    request = None
    filepath = None
    try:
        cert_filepath = utils.user_cert_file(user_url)
        request = requests.get(url,
                               cert=(cert_filepath, cert_filepath), verify=False, stream=True)

        # Registration is required
        if request.status_code == 403:
            # Update state response in meta data
            return request.text
        elif request.status_code != 200:
            raise Exception("HTTP status code: %s" % request.status_code)

        filepath = utils.url_to_download_filepath(user_url, url)
        dir = os.path.dirname(filepath);
        if not os.path.exists(dir):
            os.makedirs(dir)

        # Now we know the user is authorized, first check if they have already
        # downloaded this file.
        if os.path.exists(filepath):
            md5 = hashlib.md5()
            with open(filepath) as fp:
                for chunk in iter(partial(fp.read, 128), ''):
                    md5.update(chunk)

            # if the checksums match we can skip the download
            if checksum == md5.hexdigest():
                current_task.update_state(state='PROGRESS',  meta={'percentage': 100})
                return

        downloaded  = 0
        with open(filepath, 'w') as fp:
            for block in request.iter_content(1024):
                if not block:
                    break

                fp.write(block)
                downloaded += 1024
                # update the task state
                percentage = int((downloaded / float(size)) * 100)
                current_task.update_state(state='PROGRESS',  meta={'percentage': percentage})
    except SoftTimeLimitExceeded:
        current_task.update_state(state='CANCELED')
        # Clean up the request and files
        if request:
            request.close()
        if os.path.exists(filepath):
            os.remove(filepath)

def status(taskId):
    task = AsyncResult(taskId, backend=celery.backend)

    if not task:
        cherrypy.log("Unable to load task for id: " + taskId)

    status = {'state': str(task.state) }

    percentage = 0
    if task.state == 'PROGRESS':
        status['percentage'] = task.result['percentage']
    elif task.state == 'SUCCESS':
        if task.result:
            status['state'] = 'FORBIDDEN'
        else:
            status['percentage'] = 100
    elif task.state == 'FAILURE':
        status['message'] = str(task.result)

    return status

def cancel(taskId):
    task = AsyncResult(taskId, backend=celery.backend)
    task.revoke(celery.broker_connection(), terminate=True, signal="SIGUSR1")
