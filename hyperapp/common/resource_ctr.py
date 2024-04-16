import inspect


RESOURCE_ATTR_CTR_NAME = '__attr_resource_constructors__'
RESOURCE_MODULE_CTR_NAME = '__module_resource_constructors__'


def add_attr_constructor(module, fn_name, ctr_ref):
    ctr_dict = module.__dict__.setdefault(RESOURCE_ATTR_CTR_NAME, {})
    ctr_list = ctr_dict.setdefault(fn_name, [])
    ctr_list.append(ctr_ref)


def add_fn_module_constructor(fn, ctr_ref, name=None):
    module = inspect.getmodule(fn)
    add_attr_constructor(module, fn.__name__, ctr_ref)


def add_module_constructor(globals, ctr_ref):
    ctr_list = globals.setdefault(RESOURCE_MODULE_CTR_NAME, [])
    ctr_list.append(ctr_ref)


def add_caller_module_constructor(stack_idx, ctr_ref):
    frame = inspect.stack()[stack_idx].frame
    add_module_constructor(frame.f_globals, ctr_ref)
