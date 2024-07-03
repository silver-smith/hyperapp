from . import htypes


class ImportJob:

    @classmethod
    def from_piece(cls, piece):
        return cls()

    def __init__(self):
        pass

    def __repr__(self):
        return "<ImportJob>"

    @property
    def piece(self):
        return htypes.import_job.job()
