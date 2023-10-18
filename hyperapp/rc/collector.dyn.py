import logging

from .code.custom_resource_registry import create_custom_resource_registry
from .code.builtins_unit import BuiltinsUnit
from .code.unit import Unit, FixturesUnit, TestsUnit

log = logging.getLogger(__name__)


def collect_units(root_dir, dir_list, generator_ref, graph):
    ctx = create_custom_resource_registry(root_dir, dir_list)

    builtins_unit = BuiltinsUnit(graph, ctx)
    builtins_unit.init()

    name_to_unit = {}
    for dir in dir_list:
        for path in dir.rglob('*.dyn.py'):
            if 'test' in path.relative_to(root_dir).parts:
                continue
            name_parts = path.name[:-len('.dyn.py')].split('.')
            if name_parts[-1] == 'fixtures':
                unit = FixturesUnit(graph, ctx, generator_ref, root_dir, path)
            elif name_parts[-1] == 'tests':
                unit = TestsUnit(graph, ctx, generator_ref, root_dir, path)
            else:
                unit = Unit(graph, ctx, generator_ref, root_dir, path)
            unit.init()
            name_to_unit[unit.name] = unit

    graph.name_to_unit.update(name_to_unit)
