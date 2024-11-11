
class JobResult:

    def __init__(self, status, error=None, traceback=None):
        self.status = status
        self.error = error
        self.traceback = traceback

    @property
    def desc(self):
        return self.status.name

    def cache_target_name(self, my_target):
        return None

    @property
    def used_reqs(self):
        raise NotImplementedError()
