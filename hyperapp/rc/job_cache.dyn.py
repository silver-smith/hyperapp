from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.build import PythonModuleSrc


class CacheEntry:

    @classmethod
    def from_piece(cls, piece, rc_requirement_creg, rc_resource_creg, rc_job_result_creg):
        src = PythonModuleSrc.from_piece(piece.src)
        deps = {
            rc_requirement_creg.invite(rec.req): rc_resource_creg.invite(req.resource)
            for rec in piece.deps
            }
        result = rc_job_result_creg.invite(piece.job_result)
        return cls(piece.target_name, src, deps, result)

    def __init__(self, target_name, src, deps, result):
        self.target_name = target_name
        self._src = src
        self._deps = deps
        self._result = result

    @property
    def piece(self):
        deps = [
            htypes.job_cache.dep(
                req=mosaic.put(req.piece),
                resource=mosaic.put(resource.piece),
                )
            for req, resource in self._deps.items()
            ]
        return htypes.job_cache.entry(
            target_name=self.target_name,
            src=self._src.piece,
            deps=deps,
            job_result=mosaic.put(self._result.piece),
            )

            
class JobCache:

    def __init__(self, file_bundle, rc_requirement_creg, rc_resource_creg, rc_job_result_creg, path, load):
        self._file_bundle_factory = file_bundle
        self._rc_requirement_creg = rc_requirement_creg
        self._rc_resource_creg = rc_resource_creg
        self._rc_job_result_creg = rc_job_result_creg
        self._path = path
        self._target_to_entry = {}  # target name -> CacheEntry
        if load:
            self._load()

    def __getitem__(self, target_name):
        return self._target_to_entry[target_name]

    def put(self, target, src, deps, result):
        entry = CacheEntry(target.name, src, deps, result)
        self._target_to_entry[entry.target_name] = entry

    def save(self):
        entries = tuple(
            entry.piece for entry
            in self._target_to_entry.values()
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
        for entry_piece in piece.entries:
            entry = CacheEntry.from_piece(
                entry_piece, self._rc_requirement_creg, self._rc_resource_creg, self._rc_job_result_creg)
            self._target_to_entry[entry.target_name] = entry
