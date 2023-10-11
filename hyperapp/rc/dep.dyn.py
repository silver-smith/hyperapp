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

    @property
    def import_name(self):
        return None

    @property
    def resource_name(self):
        return None


@dataclass(eq=False)
class ServiceDep(Dep):
    service_name: str

    def __repr__(self):
        return f"service:{self.service_name}"

    @property
    def key(self):
        return self.service_name

    @property
    def import_name(self):
        return f'services.{self.service_name}'

    @property
    def resource_name(self):
        return f'{self.service_name}.service'


@dataclass(eq=False)
class CodeDep(Dep):
    code_name: str

    def __repr__(self):
        return f"code:{self.code_name}"

    @property
    def key(self):
        return self.code_name

    @property
    def import_name(self):
        return f'code.{self.code_name}'

    @property
    def resource_name(self):
        return f'{self.code_name}.module'


@dataclass(eq=False)
class FixturesDep(Dep):
    fixtures_unit_name: str

    def __repr__(self):
        return f"fixtures:{self.fixtures_unit_name}"

    @property
    def key(self):
        return self.fixtures_unit_name


@dataclass(eq=False)
class TestsDep(Dep):
    tests_unit_name: str

    def __repr__(self):
        return f"tests:{self.tests_unit_name}"

    @property
    def key(self):
        return self.tests_unit_name
