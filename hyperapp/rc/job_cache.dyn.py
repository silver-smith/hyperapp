from . import htypes
from .services import (
    mosaic,
    web,
    )


class JobCache:

    def __init__(self, file_bundle, path):
        self._file_bundle_factory = file_bundle
        self._path = path
        self._job_to_result = {}  # job piece -> result piece
        self._load()

    def get(self, job):
        return self._job_to_result.get(job.piece)

    def put(self, job, result_piece):
        self._job_to_result[job.piece] = result_piece

    def save(self):
        entries = tuple(
            htypes.job_cache.entry(
                job=mosaic.put(job),
                result=mosaic.put(result),
                )
            for job, result in self._job_to_result.items()
            )
        piece = htypes.job_cache.cache(entries)
        bundle = self._file_bundle_factory(self._path, encoding='cdr')
        bundle.save_piece(piece)
        
    def _load(self):
        bundle = self._file_bundle_factory(self._path, encoding='cdr')
        try:
            piece = bundle.load_piece(register_associations=False)
        except FileNotFoundError:
            return
        for entry in piece.entries:
            self._job_to_result[web.summon(entry.job)] = web.summon(entry.result)
