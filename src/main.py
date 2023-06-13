from worker import pipeline_fail, pipeline_ok
from celery.result import AsyncResult, states
from time import sleep
from exception import VMSTaskException
import logging
from typing import List
from pydantic import BaseModel
from uuid import UUID, uuid4

class VMSTaskState(BaseModel):
  name: str
  task_id: UUID
  state: str
  detail: str=None

class VMSTaskResult(BaseModel):
  pool_id: UUID
  pool_name: str
  state: str
  tasks: List[VMSTaskState]
  



def unpack_chain(nodes: AsyncResult): 
    while nodes.parent:
        logger.debug(f'Name in while: {nodes}')
        yield nodes
        nodes = nodes.parent
    else:
        logger.debug(f'Name in else: {nodes}')
        yield nodes
        

def unpack_states(task) -> List[VMSTaskState]:
    overall_state = []

    for task_id in task:
        result = AsyncResult(task_id)
        meta = result._get_task_meta()
        task_name = result.name or 'UNKNOWN'
        task_detail = None
        print(f'Child {task_name}, {result.task_id}, {result.status}, {str(meta)}')

        if result.state in (states.SUCCESS, 'PROGRESS'):
            task_name = task_name
            task_detail = meta['result'].get('detail')
        elif result.state in states.FAILURE:
            task_name = task_name
            task_detail = str(meta['result'])
            
        overall_state.append(VMSTaskState(name=task_name, state=result.state, task_id=result.task_id, detail=task_detail))
    
    return overall_state
        

def get_task_state(task_id: list) -> VMSTaskResult:
    task = AsyncResult(task_id[0])
    task_main_state = task.state
    task_states = unpack_states(task=task_id)
    task_states.reverse()
    result = VMSTaskResult(pool_id=uuid4(), pool_name='Test_name',
                           state=task_main_state,
                           tasks=task_states)
    
    if task.ready():
        try:
            rc = task.get(timeout=1)
            return result.dict()
        except VMSTaskException as exc:
            return result.dict()
#        except Exception as exc:
#            return (task.state, 255, None, str(exc))
    else:
        return result.dict()
    
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

task = pipeline_fail(2, 2).delay()
ids = task.as_list()
#ids.reverse()
print(ids)


while(True):
  #result = restore(ids)
  
  overall_state = get_task_state(task_id=ids)
  
  sleep(1)
  if task.ready():
    overall_state = get_task_state(task_id=ids)
    break

print('Ready')
try:
  res = task.get()
  print('Result', res)
except VMSTaskException as exc:
  print(exc)
finally:
  print('State:', task.state)

print(task)
print(overall_state)