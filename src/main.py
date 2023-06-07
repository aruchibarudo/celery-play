from worker import pipeline_fail, pipeline_ok
from celery.result import AsyncResult
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
    

task = pipeline_fail(2, 2).delay()
ids = store(task)
print(ids)


while(True):
  #result = restore(ids)
  for result in unpack_chain(task):
    meta = result._get_task_meta()
    name = result.name
    print('Child', name, result.task_id, result.status, meta)
  sleep(1)
  if task.ready():
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