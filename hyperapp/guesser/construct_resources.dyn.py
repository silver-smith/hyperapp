import logging

from . import htypes
from .services import (
    Constructor,
    ModuleVisitor,
    endpoint_registry,
    generate_rsa_identity,
    module_dir_list,
    rpc_endpoint_factory,
    subprocess_running,
    )
from .globl import GlobalVisitor

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

    constructor = Constructor(root_dir, full_module_name, module_name, module_path)

    custom_module_dirs = [*module_dir_list, module_path.parent]
    with subprocess_running(custom_module_dirs, rpc_endpoint, identity, 'guesser') as process:

        global_visitor = GlobalVisitor(
            fixtures_module=full_module_name + '.fixtures',
            on_global=constructor.on_global,
            )
        visitor = ModuleVisitor(
            on_module=constructor.on_module,
            on_global=global_visitor.run,
            )
        visitor.run(process, module_name, module_path)

    return constructor.resource_module
