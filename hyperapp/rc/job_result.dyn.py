
class JobResult:

    def __init__(self, status, error=None, traceback=None):
        self.status = status
        self.error = error
        self.traceback = traceback

    @property
    def desc(self):
        return self.status.name

    @property
    def should_cache(self):
        return False

    @property
    def used_reqs(self):
        raise NotImplementedError()
