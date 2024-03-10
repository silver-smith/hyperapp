from abc import ABCMeta, abstractproperty
from dataclasses import dataclass
from functools import total_ordering


@total_ordering
class Dep(metaclass=ABCMeta):

    def __eq__(self, rhs):
        return type(rhs) is type(self) and rhs.key == self.key

    def __hash__(self):
        return hash((type(self), self.key))

    def __lt__(self, rhs):
        if self.__class__.__name__ < rhs.__class__.__name__:
            return True
        if self.__class__.__name__ > rhs.__class__.__name__:
            return False
        return self.key < rhs.key

    @abstractproperty
    def key(self):
        pass

    @abstractproperty
    def should_be_imported(self):
        pass

    @property
    def import_name(self):
        raise NotImplementedError()

    @property
    def resource_name(self):
        raise NotImplementedError()

    def tested_override_resource(self, unit, module_res):
        raise NotImplementedError()


@dataclass(eq=False)
class ServiceDep(Dep):
    service_name: str

    def __repr__(self):
        return f"service:{self.service_name}"

    @property
    def key(self):
        return self.service_name

    @property
    def should_be_imported(self):
        return True

    @property
    def import_name(self):
        return f'services.{self.service_name}'

    @property
    def resource_name(self):
        return f'{self.service_name}.service'

    def tested_override_resource(self, unit, module_res):
        ass_list, res = unit.pick_service_resource(module_res, self.service_name)
        return res


@dataclass(eq=False)
class CodeDep(Dep):
    code_name: str

    def __repr__(self):
        return f"code:{self.code_name}"

    @property
    def key(self):
        return self.code_name

    @property
    def should_be_imported(self):
        return True

    @property
    def import_name(self):
        return f'code.{self.code_name}'

    @property
    def resource_name(self):
        return f'{self.code_name}.module'

    def tested_override_resource(self, unit, module_res):
        return module_res


@dataclass(eq=False)
class FixturesDep(Dep):
    fixtures_unit_name: str

    def __repr__(self):
        return f"fixtures:{self.fixtures_unit_name}"

    @property
    def key(self):
        return self.fixtures_unit_name

    @property
    def should_be_imported(self):
        return False


@dataclass(eq=False)
class TestsDep(Dep):
    tests_unit_name: str

    def __repr__(self):
        return f"tests:{self.tests_unit_name}"

    @property
    def key(self):
        return self.tests_unit_name

    @property
    def should_be_imported(self):
        return False


@dataclass(eq=False)
class ModuleDep(Dep):
    module_name: str

    def __repr__(self):
        return f"module:{self.module_name}"

    @property
    def key(self):
        return self.module_name

    @property
    def should_be_imported(self):
        return False
