from . import htypes
from .services import (
    rc_job_creg,
    )


class ImportJob:

    @rc_job_creg.actor(htypes.import_job.job)
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
