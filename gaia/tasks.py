from celery import Celery
from gaia.parser import parse_request
from gaia.core import config

app = Celery('tasks',
             backend=config['gaia']['celery_backend'],
             broker=config['gaia']['celery_broker'])


@app.task
def run_process(process, request_json):
    return parse_request(process, request_json)
