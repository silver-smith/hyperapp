from abc import ABCMeta, abstractproperty
from dataclasses import dataclass


class Dep(metaclass=ABCMeta):

    def __eq__(self, rhs):
        return type(rhs) is type(self) and rhs.key == self.key

    def __hash__(self):
        return hash((type(self), self.key))

    @abstractproperty
    def key(self):
        pass


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
