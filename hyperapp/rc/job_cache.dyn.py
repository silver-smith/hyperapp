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
            rc_requirement_creg.invite(rec.requirement): {
                rc_resource_creg.invite(res)
                for res in rec.resource_list
                }
            for rec in piece.deps
            }
        result = rc_job_result_creg.invite(piece.job_result)
        return cls(piece.target_name, src, deps, result)

    def __init__(self, target_name, src, deps, result):
        self.target_name = target_name
        self.src = src
        self.deps = deps
        self.result = result

    @property
    def piece(self):
        deps = [
            htypes.job_cache.dep(
                requirement=mosaic.put(req.piece),
                resource_list=tuple(
                    mosaic.put(res.piece)
                    for res in resource_set
                    )
                )
            for req, resource_set in self.deps.items()
            ]
        return htypes.job_cache.entry(
            target_name=self.target_name,
            src=self.src.piece,
            deps=tuple(deps),
            job_result=mosaic.put(self.result.piece),
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

    @staticmethod
    def _resolve_requirements(target_factory, requirements):
        deps = {}
        for req in requirements:
            target = req.get_target(target_factory)
            assert target.completed, target
            res_list = req.make_resource_list(target)
            deps[req] = set(res_list)
        return deps

    def put(self, target_factory, target_name, src, requirements, result):
        deps = self._resolve_requirements(target_factory, requirements)
        entry = CacheEntry(target_name, src, deps, result)
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
