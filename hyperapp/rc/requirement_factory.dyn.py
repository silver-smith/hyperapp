from .code.python_module_resource_target import PythonModuleReq
from .code.builtin_service_target import BuiltinServiceReq
from .code.test_requirement import TestedCodeReq, FixturesModuleReq


class RequirementFactory:

    def __init__(self, required_by_module_name):
        self._required_by_module_name = required_by_module_name

    def import_to_htype(self, import_path):
        pass

    def import_to_service(self, import_path):
        service_name = import_path[1]
        return BuiltinServiceReq(self._required_by_module_name, service_name)

    def import_to_code(self, import_path):
        code_name = import_path[1]
        return PythonModuleReq(self._required_by_module_name, code_name)

    def import_to_tested_code(self, import_path):
        code_name = import_path[2]
        return TestedCodeReq(self._required_by_module_name, import_path[:3], code_name)

    def import_to_fixtures_module(self, import_path):
        code_name = import_path[1]
        return FixturesModuleReq(import_path, code_name)

    def ignore_import(self, import_path):
        pass

    prefix_to_factory = {
        ('htypes',): import_to_htype,
        ('services',): import_to_service,
        ('code',): import_to_code,
        ('tested', 'code'): import_to_tested_code,
        ('tested',): ignore_import,
        ('fixtures',): import_to_fixtures_module,
        }

    def requirement_from_import(self, import_path):
        for prefix, factory in self.prefix_to_factory.items():
            if import_path[:len(prefix)] == prefix:
                if len(import_path) == len(prefix):
                    return None  # package import.
                return factory(self, import_path)
        raise RuntimeError(f"Unknown import kind: {'.'.join(import_path)!r}")
