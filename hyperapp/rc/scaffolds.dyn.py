from . import htypes
from .services import (
    mosaic,
    )


# Module resource with import discoverer.
def discoverer_module_res(ctx, unit):
    resource_list = [*ctx.type_recorder_res_list]

    resource_list += [
        htypes.import_recorder.resource(('services', 'mark'), mosaic.put(
            ctx.resource_registry['common.mark', 'mark.service'])),
        htypes.import_recorder.resource(('services', 'on_stop'), mosaic.put(
            ctx.resource_registry['builtins', 'on_stop.service'])),
        htypes.import_recorder.resource(('services', 'stop_signal'), mosaic.put(
            ctx.resource_registry['builtins', 'stop_signal.service'])),
        ]

    import_recorder_res = htypes.import_recorder.import_recorder(resource_list)
    import_recorder_ref = mosaic.put(import_recorder_res)
    import_discoverer_res = htypes.import_discoverer.import_discoverer()
    import_discoverer_ref = mosaic.put(import_discoverer_res)
    recorders = [import_recorder_ref, import_discoverer_ref]

    module_res = unit.make_module_res([
            htypes.builtin.import_rec('htypes.*', import_recorder_ref),
            htypes.builtin.import_rec('services.*', import_recorder_ref),
            htypes.builtin.import_rec('*', import_discoverer_ref),
            ])
    return (recorders, module_res)


def _enum_import_list(graph, dep_list, fixtures_unit):
    for dep in dep_list:
        if fixtures_unit and dep in fixtures_unit.provided_deps:
            provider = fixtures_unit
        else:
            provider = graph.dep_to_provider[dep]
        resource = provider.provided_dep_resource(dep)
        yield htypes.builtin.import_rec(dep.import_name, mosaic.put(resource))


# Module resource with import recorder.
def recorder_module_res(graph, ctx, unit, fixtures_unit=None):
    resource_list = [*ctx.type_recorder_res_list]
    import_recorder_res = htypes.import_recorder.import_recorder(resource_list)
    import_recorder_ref = mosaic.put(import_recorder_res)
    recorders = [import_recorder_ref]

    deps = graph.name_to_deps[unit.name]
    dep_imports_it = _enum_import_list(graph, deps, fixtures_unit)

    module_res = unit.make_module_res([
        htypes.builtin.import_rec('htypes.*', import_recorder_ref),
        *dep_imports_it,
        ])
    return (recorders, module_res)


def function_call_res(graph, ctx, unit, fixtures, attr):
    recorders, module_res = recorder_module_res(graph, ctx, unit, fixtures)
    attr_res = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    if attr.param_list:
        return None
        # function_res = _add_params_from_fixtures(fixtures)
        # if function_res is None:
        #     return None
    else:
        function_res = attr_res
    call_res = htypes.builtin.call(mosaic.put(function_res))
    return (recorders, call_res)
