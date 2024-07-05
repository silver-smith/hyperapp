import enum


class JobStatus(enum.Enum):
    ok = enum.auto()
    incomplete = enum.auto()
    failed = enum.auto()
