import logging

from . import htypes
from .services import (
    Constructor,
    endpoint_registry,
    generate_rsa_identity,
    module_dir_list,
    rpc_endpoint_factory,
    subprocess_running,
    )
from .custom_resource_module_registry import custom_resource_module_registry
from .attr_visitor import AttrVisitor
from .module_visitor import ModuleVisitor
from .object_visitor import ObjectVisitor

_log = logging.getLogger(__name__)


def call_n(fn_list):
    def inner(*args, **kw):
        for fn in fn_list:
            fn(*args, **kw)
    return inner


def construct_resources(full_module_name, module_name, module_path, root_dir):
    _log.info("Construct resources from: %s", full_module_name)

    identity = generate_rsa_identity(fast=True)
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)

    resource_module_reg = custom_resource_module_registry(resources_dir=module_path.parent)
    constructor = Constructor(
        resource_module_reg, root_dir, full_module_name, module_name, module_path)

    custom_module_dirs = [*module_dir_list, module_path.parent]
    with subprocess_running(custom_module_dirs, rpc_endpoint, identity, 'guesser') as process:

        attr_visitor = AttrVisitor(
            fixtures_module=resource_module_reg.get(full_module_name + '.fixtures'),
            on_attr=constructor.on_global,
            )
        object_visitor = ObjectVisitor(
            on_attr=attr_visitor.run,
            )
        module_visitor = ModuleVisitor(
            on_module=constructor.on_module,
            on_object=object_visitor.run,
            )
        module_visitor.run(process, module_name, module_path)

    return constructor.resource_module
