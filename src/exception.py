class TaskException(Exception):
  task_name: str = None
  
  def __init__(self, task_name: str=None, *args: object) -> None:
    super().__init__(*args)
    self.task_name = task_name