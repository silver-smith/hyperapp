from .code.rc_target import TargetMissingError, Target
from .code.import_resource import ImportResource


class TypeTarget(Target):

    @staticmethod
    def target_name(module_name, name):
        return f'type/{module_name}/{name}'

    def __init__(self, types, module_name, name):
        self._types = types
        self._module_name = module_name
        self._name = name

    @property
    def name(self):
        return self.target_name(self._module_name, self._name)

    @property
    def completed(self):
        return True

    @property
    def resource(self):
        try:
            src = self._types.as_src_dict[self._module_name][self._name]
        except KeyError:
            raise TargetMissingError(f"Type is missing: {self._module_name}.{self._name}")
        return ImportResource.from_type_src(src)
