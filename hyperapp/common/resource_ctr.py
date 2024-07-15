import inspect


RESOURCE_MODULE_CTR_NAME = '__module_resource_constructors__'


def add_module_constructor(globals, ctr_ref):
    ctr_list = globals.setdefault(RESOURCE_MODULE_CTR_NAME, [])
    ctr_list.append(ctr_ref)


def add_fn_module_constructor(fn, ctr_ref):
    module = inspect.getmodule(fn)
    add_module_constructor(module.__dict__, ctr_ref)


def add_caller_module_constructor(stack_idx, ctr_ref):
    frame = inspect.stack()[stack_idx].frame
    add_module_constructor(frame.f_globals, ctr_ref)
