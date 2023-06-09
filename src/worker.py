from celery import Celery, states
from celery.result import AsyncResult
import logging
from exception import TaskException
from time import sleep

REDIS = 'redis://localhost/0'

logger = logging.getLogger(__name__)

app = Celery('worker', broker=REDIS, backend=REDIS)
app.conf.update(result_extended=True)


@app.task(name='_Add', bind=True)
def add(self, x, y):
  logger.info('Run x + y')
  self.update_state(state=states.state('PROGRESS'), meta={'task': self.name})
  sleep(2)
  self.update_state(state=states.SUCCESS, meta={'task': self.name})
  return x + y


@app.task(name='_Fail', bind=True)
def fail(self, x, y):
  logger.info('Run fail task')
  self.update_state(state=states.state('PROGRESS'), meta={'task': self.name})
  sleep(2)
  logger.error('Error as expected')
  raise TaskException('Failed task', self.name)


@app.task(name='_Success', bind=True)
def success(self, res):
  logger.info('Task is finished')
  self.update_state(state=states.state('PROGRESS'), meta={'task': self.name})
  sleep(2)
  self.update_state(state=states.SUCCESS, meta={'task': self.name})
  return res


@app.task(name='_Error', bind=True)
def error(self, task):
  logger.error('Pipeline failed')
  res = AsyncResult(task)
  return res.state


def pipeline_ok(x, y):
  logger.info('Start pipeline_ok')
  chain = (add.si(x, y) | add.s(4) | add.s(6) | success.s()).on_error(error.s())
  return chain
  

def pipeline_fail(x, y):
  logger.info('Start pipeline_fail')
  chain = (add.si(x, y) | fail.s(4) | success.s()).on_error(error.s())
  return chain


