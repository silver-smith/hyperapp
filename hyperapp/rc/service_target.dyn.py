from dataclasses import dataclass

from . import htypes
from .services import (
    builtin_services,
    )
from .code.rc_target import Target
from .code.rc_requirement import Requirement
from .code.import_resource import ImportResource


# Unused. Is it really needed?`
@dataclass(frozen=True, unsafe_hash=True)
class ServiceFoundReq(Requirement):

    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name)

    @property
    def piece(self):
        return htypes.service.service_found_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.service_found(self.service_name)

    def make_resource(self, target):
        raise NotImplementedError(f"ServiceFoundReq is never actually used: {self.service_name!r}")


@dataclass(frozen=True, unsafe_hash=True)
class ServiceCompleteReq(Requirement):

    service_name: str

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.service_name)

    @property
    def piece(self):
        return htypes.service.service_complete_req(self.service_name)

    def get_target(self, target_factory):
        return target_factory.service_complete(self.service_name)

    def make_resource(self, target):
        return ImportResource(['services', self.service_name], target.service_piece)


class ServiceFoundTarget(Target):

    @staticmethod
    def target_name(service_name):
        return f'service_found/{service_name}'

    def __init__(self, service_name, all_imports_known_tgt):
        self._service_name = service_name
        self._all_imports_known_tgt = all_imports_known_tgt
        self._completed = service_name in builtin_services
        self._provider_resource_tgt = None
        self._ctr = None
        self._import_alias_tgt = None
        self._unresolved_in_tests = set()  # tests were imported while provider was not yet discovered.

    @property
    def name(self):
        return self.target_name(self._service_name)

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        if self._import_alias_tgt:
            return {self._import_alias_tgt}
        else:
            return {self._all_imports_known_tgt}

    def update_status(self):
        if self._completed:
            return
        if self._provider_resource_tgt and self._provider_resource_tgt.completed:
            self._completed = True
        elif self._import_alias_tgt and self._import_alias_tgt.completed:
            self._completed = True

    def set_provider(self, resource_tgt, ctr, target_set):
        self._provider_resource_tgt = resource_tgt
        self._ctr = ctr
        self._import_alias_tgt = resource_tgt.import_alias_tgt
        for test_target in self._unresolved_in_tests:
            resource_tgt.add_test(test_target, target_set)
        self.update_status()

    def add_unresolved_in_test(self, test_target):
        self._unresolved_in_tests.add(test_target)

    @property
    def import_alias_tgt(self):
        return self._import_alias_tgt

    @property
    def provider_resource_tgt(self):
        return self._provider_resource_tgt

    @property
    def constructor(self):
        return self._ctr


# Tests passed, have enough info for construction.
class ServiceResolvedTarget(Target):

    @staticmethod
    def target_name(service_name):
        return f'service-resolved/{service_name}'

    def __init__(self, service_name, ready_tgt):
        self._service_name = service_name
        self._is_builtin = service_name in builtin_services
        self._completed = self._is_builtin
        self._ready_tgt = ready_tgt
        self._provider_resource_tgt = None
        self._ctr = None

    @property
    def name(self):
        return self.target_name(self._service_name)

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        if self._is_builtin:
            return set()
        return {self._ready_tgt}

    @property
    def provider_resource_tgt(self):
        assert not self._is_builtin
        return self._provider_resource_tgt

    @property
    def constructor(self):
        assert self._completed
        return self._ctr

    def resolve(self, ctr):
        assert not self._is_builtin
        self._ctr = ctr
        self._provider_resource_tgt = self._ready_tgt.provider_resource_tgt
        self._completed = True


class ServiceCompleteTarget(Target):

    @staticmethod
    def target_name_for_service_name(service_name):
        return f'service_complete/{service_name}'

    def __init__(self, service_name, service_resolved_tgt):
        self._service_name = service_name
        self._resolved_tgt = service_resolved_tgt
        self._provider_resource_tgt = None
        self._is_builtin = service_name in builtin_services
        self._completed = self._is_builtin

    @property
    def name(self):
        return self.target_name_for_service_name(self._service_name)

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        if self._is_builtin:
            return set()
        if self._provider_resource_tgt:
            return {self._resolved_tgt, self._provider_resource_tgt}
        else:
            return {self._resolved_tgt}

    def update_status(self):
        if self._completed or self._is_builtin:
            return
        if not self._provider_resource_tgt and self._resolved_tgt.completed:
            self._provider_resource_tgt = self._resolved_tgt.provider_resource_tgt
        if self._provider_resource_tgt:
            self._completed = self._provider_resource_tgt.completed

    @property
    def provider_resource_tgt(self):
        assert not self._is_builtin
        return self._provider_resource_tgt

    @property
    def service_piece(self):
        if self._is_builtin:
            return htypes.builtin.builtin_service(self._service_name)
        else:
            ctr = self._resolved_tgt.constructor
            return self._provider_resource_tgt.get_resource_component(ctr)
