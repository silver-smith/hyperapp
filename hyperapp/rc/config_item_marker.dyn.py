import inspect

from .code.service_ctr import ConfigItemFixtureCtr


def config_item_fixture_marker(service_name, module_name, ctr_collector):
    def _config_item_fixture_wrapper(fn):
        ctr = ConfigItemFixtureCtr(
            module_name=module_name, 
            attr_qual_name=fn.__qualname__.split('.'),
            service_name=service_name,
            service_params=tuple(inspect.signature(fn).parameters),
            )
        ctr_collector.add_constructor(ctr)
        return fn
    return _config_item_fixture_wrapper
