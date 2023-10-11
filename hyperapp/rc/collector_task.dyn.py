import logging

from .code.custom_resource_registry import create_custom_resource_registry
from .code.builtins_unit import BuiltinsUnit
from .code.source_file_unit import SourceFileUnit

log = logging.getLogger(__name__)


class CollectorTask:

    def __init__(self, generator_ref, root_dir, dir_list):
        self._generator_ref = generator_ref
        self._root_dir = root_dir
        self._dir_list = dir_list

    def run(self, graph):
        ctx = create_custom_resource_registry(self._root_dir, self._dir_list)

        builtins_unit = BuiltinsUnit(ctx)
        builtins_unit.init(graph)

        name_to_unit = {}
        for dir in self._dir_list:
            for path in dir.rglob('*.dyn.py'):
                if 'test' in path.relative_to(self._root_dir).parts:
                    continue
                unit = SourceFileUnit(ctx, self._generator_ref, self._root_dir, path)
                unit.init(graph)
                name_to_unit[unit.name] = unit

        graph.name_to_unit.update(name_to_unit)
