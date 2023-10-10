from dataclasses import dataclass


@dataclass
class ServiceDep:
    service_name: str

    def __repr__(self):
        return f"service:{self.service_name}"

    def __eq__(self, rhs):
        return type(rhs) is ServiceDep and rhs.service_name == self.service_name

    def __hash__(self):
        return hash((type(self), self.service_name))


@dataclass
class CodeDep:
    code_name: str

    def __repr__(self):
        return f"code:{self.code_name}"

    def __eq__(self, rhs):
        return type(rhs) is CodeDep and rhs.code_name == self.code_name

    def __hash__(self):
        return hash((type(self), self.code_name))
