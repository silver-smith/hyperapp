
class JobResult:

    def __init__(self, status, error=None, traceback=None):
        self.status = status
        self.error = error
        self.traceback = traceback
