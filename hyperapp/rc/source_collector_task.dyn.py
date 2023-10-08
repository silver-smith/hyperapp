import logging

from .code.custom_resource_registry import create_custom_resource_registry
from .code.source_file_unit import SourceFileUnit

log = logging.getLogger(__name__)


class SourceCollectorTask:

    def __init__(self, generator_ref, root_dir, dir_list):
        self._generator_ref = generator_ref
        self._root_dir = root_dir
        self._dir_list = dir_list

    def submit(self, graph):
        ctx = create_custom_resource_registry(self._root_dir, self._dir_list)

        name_to_unit = {}
        for dir in self._dir_list:
            for path in dir.rglob('*.dyn.py'):
                if 'test' in path.relative_to(self._root_dir).parts:
                    continue
                unit = SourceFileUnit(self._generator_ref, self._root_dir, path)
                unit.init(graph, ctx)
                name_to_unit[unit.name] = unit

        outdated_units = [u for u in name_to_unit.values() if not u.is_up_to_date(graph)]
        tasks = []
        for unit in outdated_units:
            if unit.is_tests:
                tasks += unit.make_tasks(ctx)
        return tasks
