from . import htypes


class ImportJob:

    def __init__(self):
        pass

    def __repr__(self):
        return "<ImportJob>"

    @property
    def piece(self):
        return htypes.import_job.job()
