import logging

from . import htypes
from .services import (
    constructor_creg,
    mosaic,
    )

log = logging.getLogger(__name__)


def invite_attr_constructors(ctx, attr_list, module_res, name_to_res):
    ass_list = []
    for attr in attr_list:
        for ctr_ref in attr.constructors:
            ass_list += constructor_creg.invite(ctr_ref, ctx.types, name_to_res, module_res, attr) or []
    return ass_list


def invite_module_constructors(ctx, ctr_list, module_res, name_to_res):
    ass_list = []
    for ctr_ref in ctr_list:
        ass_list += constructor_creg.invite(ctr_ref, ctx.types, name_to_res, module_res) or []
    return ass_list


# Module resource with import discoverer.
def discoverer_module_res(ctx, unit):
    resource_list = (*ctx.type_recorder_res_list,)

    resource_list += (
        htypes.import_recorder.resource(('services', 'mark'), mosaic.put(
            ctx.resource_registry['common.mark', 'mark.service'])),
        htypes.import_recorder.resource(('services', 'on_stop'), mosaic.put(
            ctx.resource_registry['builtins', 'on_stop.service'])),
        htypes.import_recorder.resource(('services', 'stop_signal'), mosaic.put(
            ctx.resource_registry['builtins', 'stop_signal.service'])),
        )

    import_recorder_res = htypes.import_recorder.import_recorder(unit.name, resource_list)
    import_recorder_ref = mosaic.put(import_recorder_res)
    import_discoverer_res = htypes.import_discoverer.import_discoverer(unit.name)
    import_discoverer_ref = mosaic.put(import_discoverer_res)
    recorders = {unit.name: [import_recorder_ref, import_discoverer_ref]}

    module_res = unit.make_module_res([
            htypes.builtin.import_rec('htypes.*', import_recorder_ref),
            htypes.builtin.import_rec('services.*', import_recorder_ref),
            htypes.builtin.import_rec('*', import_discoverer_ref),
            ])
    return (recorders, module_res)


def enum_dep_imports(graph, dep_set, fixtures_unit=None, fixtures_module_res=None):
    for dep in dep_set:
        if not dep.should_be_imported:
            continue
        if fixtures_module_res and dep in fixtures_unit.provided_deps:
            resource = dep.tested_override_resource(fixtures_unit, fixtures_module_res)
        else:
            if fixtures_unit and dep in fixtures_unit.provided_deps:
                provider = fixtures_unit
            else:
                provider = graph.dep_to_provider[dep]
            resource = provider.provided_dep_resource(dep)
        yield htypes.builtin.import_rec(dep.import_name, mosaic.put(resource))


def types_import_list(ctx, import_set):
    return {
        htypes.builtin.import_rec(
            f'htypes.{pair[0]}.{pair[1]}',
            mosaic.put(ctx.type_pair_to_resource[pair]),
            )
        for pair in import_set
        }


# Module resource with import recorder.
def recorder_module_res(graph, ctx, unit, fixtures_unit=None, fixtures_module_res=None, import_list=None):
    resource_list = tuple(ctx.type_recorder_res_list)
    import_recorder_res = htypes.import_recorder.import_recorder(unit.name, resource_list)
    import_recorder_ref = mosaic.put(import_recorder_res)
    recorders = {unit.name: [import_recorder_ref]}

    dep_imports_it = enum_dep_imports(graph, unit.deps, fixtures_unit, fixtures_module_res)

    module_res = unit.make_module_res([
        htypes.builtin.import_rec('htypes.*', import_recorder_ref),
        *dep_imports_it,
        *(import_list or []),
        ])
    return (recorders, module_res)


def _parameter_fixture(fixtures, path):
    name = '.'.join([*path, 'parameter'])
    try:
        return fixtures.resource(name)
    except KeyError:
        return None


# Warning: never tested yet.
def _partial_res(unit, fixtures, attr, attr_res):
    attr_path = [attr.name]
    attr_path_str = '.'.join(attr_path)
    kw = {
        param: _parameter_fixture(fixtures, [*attr_path, param])
        for param in attr.param_list
        }
    kw = {key: value for key, value in kw.items() if value is not None}
    log.info("%s:%s: Parameter fixtures: %s", unit.name, attr_path_str, kw)
    missing_params = ", ".join(sorted(set(attr.param_list) - set(kw)))
    if missing_params:
        if kw:
            raise RuntimeError(f"Some parameter fixtures are missing for {unit.name}:{attr_path_str}: {missing_params}")
        else:
            # All are missing - guess this function is not intended to be tested using fixture parameters.
            log.warning("Parameter fixtures are missing for %s:%s: %s; won't call", unit.name, attr_path_str, missing_params)
            return None
    return htypes.partial.partial(
        function=mosaic.put(attr_res),
        params=tuple(
            htypes.partial.param(name, mosaic.put(value))
            for name, value in kw.items()
            ),
        )


def function_call_res(graph, ctx, unit, fixtures, attr):
    recorders, module_res = recorder_module_res(graph, ctx, unit, fixtures)
    attr_res = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    if attr.param_list:
        if not fixtures:
            log.warning("Fixtures module is missing for %s:%s parameters; won't call", unit.name, attr.name)
            return None
        function_res = _partial_res(unit, fixtures, attr, attr_res)
        if not function_res:
            return None
    else:
        function_res = attr_res
    call_res = htypes.builtin.call(mosaic.put(function_res))
    return (recorders, module_res, call_res)


# def tested_import_list(graph, ctx, test_unit, tested_units, tested_service_to_unit):
#     import_list = []
#     all_recorders = {}
#     for unit in tested_units:
#         recorders, module_res = recorder_module_res(graph, ctx, unit, fixtures_unit=test_unit)
#         all_recorders.update(recorders)
#         import_rec = htypes.builtin.import_rec(f'tested.code.{unit.code_name}', mosaic.put(module_res))
#         import_list.append(import_rec)
#     all_ass_list = []
#     for service_name, unit in tested_service_to_unit.items():
#         recorders, module_res = recorder_module_res(graph, ctx, unit, fixtures_unit=test_unit)
#         all_recorders.update(recorders)
#         ass_list, service_res = unit.pick_service_resource(module_res, service_name)
#         all_ass_list += ass_list
#         import_rec = htypes.builtin.import_rec(f'tested.services.{service_name}', mosaic.put(service_res))
#         import_list.append(import_rec)
#     return (all_recorders, all_ass_list, import_list)


def tested_units(graph, ctx, test_unit, fixtures_module_res, tested_units):
    field_list = []
    all_recorders = {}
    ass_list = []
    for unit in tested_units:
        recorders, module_res = recorder_module_res(graph, ctx, unit, fixtures_unit=test_unit, fixtures_module_res=fixtures_module_res)
        ass_list += unit.attr_constructors_associations(module_res)
        all_recorders.update(recorders)
        field = htypes.inspect.tested_unit(unit.name, unit.code_name, mosaic.put(module_res))
        field_list.append(field)
    return (all_recorders, ass_list, field_list)


def tested_services(graph, ctx, test_unit, fixtures_module_res, tested_service_to_unit):
    field_list = []
    all_recorders = {}
    ass_list = []
    for service_name, unit in tested_service_to_unit.items():
        recorders, module_res = recorder_module_res(graph, ctx, unit, fixtures_unit=test_unit, fixtures_module_res=fixtures_module_res)
        all_recorders.update(recorders)
        unit_ass_list, service_res = unit.pick_service_resource(module_res, service_name)
        ass_list += unit_ass_list
        field = htypes.inspect.field(service_name, mosaic.put(service_res))
        field_list.append(field)
    return (all_recorders, ass_list, field_list)


def test_call_res(graph, ctx, unit, attr):
    import_list = [
        htypes.builtin.import_rec('tested.code.*', mosaic.put(htypes.tested_imports.tested_import())),
        htypes.builtin.import_rec('tested.services.*', mosaic.put(htypes.tested_imports.tested_import())),
        ]
    recorders, module_res = recorder_module_res(graph, ctx, unit, import_list=import_list)
    attr_res = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    if attr.param_list:
        raise RuntimeError(f"{unit.name}: Test {attr.name} wants parameters, but that's not supported")
    call_res = htypes.builtin.call(mosaic.put(attr_res))
    return (recorders, module_res, call_res)
