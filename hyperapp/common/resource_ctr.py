import inspect


RESOURCE_ATTR_CTR_NAME = '__resource_constructors__'


def add_attr_constructor(module, fn_name, ctr_ref):
    ctr_dict = module.__dict__.setdefault(RESOURCE_ATTR_CTR_NAME, {})
    ctr_list = ctr_dict.setdefault(fn_name, [])
    ctr_list.append(ctr_ref)


def add_fn_module_constructor(fn, ctr_ref, name=None):
    module = inspect.getmodule(fn)
    add_attr_constructor(module, fn.__name__, ctr_ref)
