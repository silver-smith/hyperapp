from . import htypes
from .services import (
    mosaic,
    web,
    )


class JobCache:

    def __init__(self, file_bundle, path):
        self._file_bundle_factory = file_bundle
        self._path = path
        self._target_to_job_result = {}  # job piece -> result piece
        self._load()

    def get(self, target, job):
        try:
            job_piece, result_piece = self._target_to_job_result[target.name]
        except KeyError:
            return None
        if job.piece == job_piece:
            return result_piece
        else:
            return None

    def put(self, target, job, result_piece):
        self._target_to_job_result[target.name] = (job.piece, result_piece)

    def save(self):
        entries = tuple(
            htypes.job_cache.entry(
                target_name=target_name,
                job=mosaic.put(job),
                result=mosaic.put(result),
                )
            for target_name, (job, result) in self._target_to_job_result.items()
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
            self._target_to_job_result[entry.target_name] = (
                web.summon(entry.job),
                web.summon(entry.result),
                )
