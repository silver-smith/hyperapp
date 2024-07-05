
class JobResult:

    def __init__(self, status, message=None, traceback=None):
        self.status = status
        self.message = message
        self.traceback = traceback
