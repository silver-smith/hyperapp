import inspect

from .code.fixture_ctr import ConfigFixtureCtr, ConfigTemplateFixtureCtr


def config_fixture_marker(service_name, module_name, ctr_collector):
    def _config_fixture_wrapper(fn):
        ctr = ConfigFixtureCtr(
            module_name=module_name, 
            attr_qual_name=fn.__qualname__.split('.'),
            service_name=service_name,
            service_params=tuple(inspect.signature(fn).parameters),
            )
        ctr_collector.add_constructor(ctr)
        return fn
    return _config_fixture_wrapper


def config_template_fixture_marker(service_name, module_name, ctr_collector):
    def _config_template_fixture_wrapper(fn):
        service_params = tuple(inspect.signature(fn).parameters)
        ctr = ConfigTemplateFixtureCtr(
            module_name=module_name,
            attr_qual_name=fn.__qualname__.split('.'),
            service_name=service_name,
            service_params=tuple(inspect.signature(fn).parameters),
            )
        ctr_collector.add_constructor(ctr)
        return fn
    return _config_template_fixture_wrapper
