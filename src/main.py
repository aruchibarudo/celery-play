from worker import pipeline_fail, pipeline_ok
from celery.result import AsyncResult, states
from time import sleep
from exception import TaskException


def store(node):
    id_chain = []
    while node.parent:
      id_chain.append(node.id)
      node = node.parent
    id_chain.append(node.id)
    return id_chain

def restore(id_chain) -> AsyncResult:
    id_chain.reverse()
    last_result = None
    for tid in id_chain:
        result = AsyncResult(tid)
        result.parent = last_result
        last_result = result
    return last_result
  
def unpack_chain(nodes: AsyncResult): 
    while nodes.parent:
        yield nodes
        nodes = nodes.parent
    else:
      yield nodes
    

task = pipeline_ok(2, 2).delay()
ids = task.as_list()
print(ids)

overall_state = {}

while(True):
  #result = restore(ids)
  
  for result in unpack_chain(task):
    meta = result._get_task_meta()
    name = result.name
    print('Child', name, result.task_id, result.status, meta)

  
  sleep(1)
  if task.ready():
    for result in unpack_chain(task):
      meta = result._get_task_meta()
      name = result.name
      
      if result.state in (states.SUCCESS, states.state('PROGRESS')):
        task_name = meta['result']['task']
        overall_state[task_name] = result.state
      elif result.state in states.FAILURE:
        task_name = meta['result'].task_name
        overall_state[task_name] = result.state    
        
      print('Child', name, result.task_id, result.status, meta)

    break

print('Ready')
try:
  res = task.get()
  print('Result', res)
except TaskException as exc:
  print(exc)
finally:
  print('State:', task.state)

print(task)
print(overall_state)