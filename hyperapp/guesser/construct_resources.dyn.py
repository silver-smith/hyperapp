import logging

from . import htypes
from .services import (
    Constructor,
    endpoint_registry,
    load_additional_modules_ref,
    generate_rsa_identity,
    module_dir_list,
    rpc_endpoint_factory,
    subprocess_running,
    )
from .custom_resource_module_registry import load_custom_resources
from .import_resources import available_import_resources, override_import_resources_with_fixtures
from .attr_visitor import AttrVisitor
from .module_visitor import ModuleVisitor
from .object_visitor import ObjectVisitor

_log = logging.getLogger(__name__)


def call_n(fn_list):
    def inner(*args, **kw):
        for fn in fn_list:
            fn(*args, **kw)
    return inner



process_code_module_list = [
    'common.lcs',
    'ui.impl_registry',
    'ui.global_command_list',
    ]


def construct_resources(resource_dir_list, full_module_name, module_name, module_path, root_dir):
    _log.info("Additional resource dirs: %s", resource_dir_list)
    _log.info("Construct resources from: %s", full_module_name)

    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)

    custom_resources = load_custom_resources(resources_dir=module_path.parent)
    fixtures_module = custom_resources.res_module_reg.get(full_module_name + '.fixtures')
    import_resources = dict(available_import_resources(custom_resources))
    overridden_import_resources = override_import_resources_with_fixtures(import_resources, fixtures_module)
    constructor = Constructor(
        custom_resources.res_module_reg, fixtures_module, import_resources,
        root_dir, full_module_name, module_name, module_path)

    with subprocess_running(
            module_dir_list,
            process_code_module_list,
            rpc_endpoint,
            identity,
            'guesser',
        ) as process:

        load_additional_modules = process.rpc_call(load_additional_modules_ref)
        load_additional_modules([str(module_path.parent)])

        attr_visitor = AttrVisitor(
            fixtures_module=fixtures_module,
            on_attr=constructor.on_attr,
            )
        object_visitor = ObjectVisitor(
            on_attr=attr_visitor.run,
            )
        global_attr_visitor = AttrVisitor(
            fixtures_module=fixtures_module,
            on_attr=constructor.on_global,
            on_object=object_visitor.run,
            )
        global_visitor = ObjectVisitor(
            on_attr=global_attr_visitor.run,
            )
        module_visitor = ModuleVisitor(
            overridden_import_resources,
            on_module=constructor.on_module,
            on_object=global_visitor.run,
            )
        module_visitor.run(process, module_name, module_path)

    return constructor.resource_module
