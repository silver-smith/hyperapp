import logging
from collections import defaultdict
from functools import partial

from . import htypes
from .services import (
    cached_code_registry_ctr,
    code_registry_ctr,
    pyobj_creg,
    )
from .code.config_ctl import DictConfigCtl, service_pieces_to_config
from .code.config_layer import ProjectConfigLayer, StaticConfigLayer
from .code.service_template import service_template_cfg_item_config, service_template_cfg_value_config
from .code.actor_template import actor_template_cfg_item_config, actor_template_cfg_value_config

log = logging.getLogger(__name__)


class ServiceDepLoopError(Exception):
    pass


class UnknownServiceError(Exception):

    def __init__(self, service_name):
        super().__init__(f"Unknown service: {service_name!r}")
        self.service_name = service_name


class System:

    _system_name = "System"

    def __init__(self):
        self._name_to_layer = {}  # layer name -> layer.
        self._config_templates_cache = None
        self._name_to_service = {}
        self._resolve_stack = {}  # service name -> requester
        self._finalizers = {}  # service name -> fn
        self._config_hooks = []
        self._default_layer_name = None
        self._init()

    def _init(self):
        config_ctl_creg_config = self._make_config_ctl_creg_config()
        self._config_ctl_creg = code_registry_ctr('config_ctl_creg', config_ctl_creg_config)
        # cfg_item_creg and cfg_value_creg are used by DictConfigCtl.
        self._cfg_item_creg = cached_code_registry_ctr('cfg_item_creg', self._make_cfg_item_creg_config())
        self._cfg_value_creg = code_registry_ctr('cfg_value_creg', self._make_cfg_value_creg_config())
        config_ctl_creg_config[htypes.system.dict_config_ctl] = partial(
            DictConfigCtl.from_piece, cfg_item_creg=self._cfg_item_creg, cfg_value_creg=self._cfg_value_creg)
        self._dict_config_ctl = DictConfigCtl(self._cfg_item_creg, self._cfg_value_creg)
        self._config_ctl = self._make_config_ctl({
            'system': self._dict_config_ctl,
            'config_ctl_creg': self._dict_config_ctl,
            'cfg_item_creg': self._dict_config_ctl,
            'cfg_value_creg': self._dict_config_ctl,
            })
        self.add_core_service('cfg_item_creg', self._cfg_item_creg)
        self.add_core_service('cfg_value_creg', self._cfg_value_creg)
        self.add_core_service('config_ctl_creg', self._config_ctl_creg)
        self.add_core_service('config_ctl', self._config_ctl)
        self.add_core_service('get_layer_config_templates', self.get_layer_config_templates)
        self.add_core_service('get_system_config_piece', self.get_config_piece)
        self.add_core_service('system', self)

    def _make_config_ctl_creg_config(self):
        return {}

    def _make_config_ctl(self, config):
        return config

    def _make_cfg_item_creg_config(self):
        return {
            **service_template_cfg_item_config(),
            **actor_template_cfg_item_config(),
            }

    def _make_cfg_value_creg_config(self):
        return {
            **service_template_cfg_value_config(),
            **actor_template_cfg_value_config(),
            }

    @property
    def name_to_layer(self):
        return self._name_to_layer

    @property
    def service_names(self):
        return {*self._name_to_template, *self._name_to_service}

    def add_core_service(self, name, service):
        self._name_to_service[name] = service
        self._config_ctl[name] = self._dict_config_ctl

    def add_config_hook(self, hook):
        self._config_hooks.append(hook)
        self._call_config_hooks([hook])

    def update_service_config(self, service_name, config):
        try:
            dest = self._config_templates[service_name]
        except KeyError:
            ctl = self._config_ctl[service_name]
            dest = ctl.empty_config_template()
            self._config_templates[service_name]= dest
        dest.update(config)

    def update_service_own_config(self, service_name, config_template):
        service = self._name_to_service[service_name]
        for key, item in config_template.items():
            value = self._cfg_value_creg.animate(item, key, self, service_name)
            service.update_config({key: value})

    def update_config_ctl(self, system_config):
        for service_name, item in system_config.items():
            self._config_ctl[service_name] = self._config_ctl_creg.invite(item.ctl)

    def load_static_config(self, config_piece):
        layer = StaticConfigLayer(self, self['config_ctl'], config_piece)
        self.load_config_layer('full', layer)

    def load_projects(self, projects):
        for project in projects:
            layer = ProjectConfigLayer(self, self['config_ctl'], project)
            self._load_config_layer(project.name, layer)
        self.invalidate_config_cache()
        self._call_config_hooks(self._config_hooks)

    def load_config_layer(self, layer_name, layer):
        self._load_config_layer(layer_name, layer)
        self.invalidate_config_cache()
        self._call_config_hooks(self._config_hooks)

    def _load_config_layer(self, layer_name, layer):
        # layer.config is expected to be ordered with service_config_order.
        log.debug("Load config layer: %r; services: %s", layer_name, list(layer.config))
        self._name_to_layer[layer_name] = layer

    def config_item_was_set(self, service_name, key):
        self.invalidate_config_cache()
        self._call_config_hooks_for_key(service_name, key, lambda hook: hook.config_item_set)

    def _call_config_hooks_for_key(self, service_name, key, hook_method):
        ctl = self._config_ctl[service_name]
        if not ctl.is_multi_item:
            return  # No hooks for non-multi-item configs.
        config_template = self._config_templates[service_name]
        item_list = ctl.config_to_items(config_template)
        for kv in item_list:
            if kv[0] != key:
                continue
            for hook in self._config_hooks:
                hook_method(hook)(service_name, kv)

    def config_item_was_removed(self, service_name, key):
        self.invalidate_config_cache()
        self._call_config_hooks_for_key(service_name, key, lambda hook: hook.config_item_removed)

    def _call_config_hooks(self, hook_list):
        for service_name, config_template in self._config_templates.items():
            ctl = self._config_ctl[service_name]
            if not ctl.is_multi_item:
                continue  # No hooks for non-multi-item configs.
            item_list = ctl.config_to_items(config_template)
            for kv in item_list:
                for hook in hook_list:
                    hook.config_item_set(service_name, kv)

    def service_config_order(self, service_name):
        order = {
            'cfg_item_creg': 1,
            'cfg_value_creg': 1,
            'config_ctl_creg': 2,
            'system': 3,
            }
        return order.get(service_name, 10)

    def set_default_layer(self, layer_name):
        self._default_layer_name = layer_name

    @property
    def default_layer(self):
        if self._default_layer_name:
            return self._name_to_layer[self._default_layer_name]
        return list(self._name_to_layer.values())[-1]

    def get_layer_config_templates(self, layer_name):
        layer = self._name_to_layer[layer_name]
        return self._collect_layers_configs([layer])

    def get_config_piece(self):
        return self.config_to_data(self._config_templates)

    def config_to_data(self, service_to_config):
        service_to_config_piece = {}
        for service_name, config in service_to_config.items():
            ctl = self._config_ctl[service_name]
            service_to_config_piece[service_name] = ctl.to_data(config)
        return service_pieces_to_config(service_to_config_piece)
        
    def get_config_template(self, service_name):
        try:
            return self._config_templates[service_name]
        except KeyError:
            ctl = self._config_ctl[service_name]
            return ctl.empty_config_template()

    def invalidate_config_cache(self):
        self._config_templates_cache = None

    def _collect_layers_configs(self, layer_list):
        service_to_config = dict()
        for layer in layer_list:
            for service_name, config in layer.config.items():
                ctl = self._config_ctl[service_name]
                try:
                    dest = service_to_config[service_name]
                except KeyError:
                    dest = ctl.empty_config_template()
                dest = ctl.merge(dest, config)
                service_to_config[service_name] = dest
        return service_to_config

    @property
    def _config_templates(self):
        if self._config_templates_cache is not None:
            return self._config_templates_cache
        service_to_config = self._collect_layers_configs(self._name_to_layer.values())
        self._config_templates_cache = service_to_config
        return service_to_config

    @property
    def _name_to_template(self):
        return self._config_templates.get('system', {})

    def run(self, root_name, *args, **kw):
        service = self.resolve_service(root_name)
        log.info("%s: run root service %s: %s", self._system_name, root_name, service)
        try:
            return self._run_service(service, args, kw)
        finally:
            self.close()
            log.info("%s: stopped", self._system_name)

    def _run_service(self, service, args, kw):
        return service(*args, **kw)

    def resolve_config(self, service_name):
        config_template = self.get_config_template(service_name)
        ctl = self._config_ctl[service_name]
        return ctl.resolve(self, service_name, config_template)

    def __getitem__(self, service_name):
        return self.resolve_service(service_name)

    def resolve_service(self, name, requester=None):
        try:
            return self._name_to_service[name]
        except KeyError:
            pass
        # ConfigItemMissing(KeyError) can be fired here, should be out of try/except KeyError.
        name_to_template = self._name_to_template
        try:
            template = name_to_template[name]
        except KeyError:
            self._raise_missing_service(name)
        if name in self._resolve_stack:
            self._raise_service_loop(name, requester)
        self._resolve_stack[name] = requester
        try:
            service = self._cfg_value_creg.animate(template, name, self, 'system')
        finally:
            self._resolve_stack.popitem()
        self._name_to_service[name] = service
        return service

    def bind_services(self, fn, params, requester=None):
        service_kw = {
            name: self.resolve_service(name, requester)
            for name in params
            }
        return partial(fn, **service_kw)

    def _raise_service_loop(self, name, requester):
        stack = [
            *self._resolve_stack.items(),
            (name, requester),
            ]
        svc_list = [
            f"{req} -> {name}" if req else name
            for name, req in stack
            ]
        loop = " -> ".join(svc_list)
        raise ServiceDepLoopError(f"Service dependency loop: {loop}")

    def add_finalizer(self, service_name, finalizer):
        self._finalizers[service_name] = finalizer

    def close(self):
        log.info("%s: run %d finalizers:", self._system_name, len(self._finalizers))
        for name, fn in reversed(self._finalizers.items()):
            log.info("%s: call finalizer for %r: %s", self._system_name, name, fn)
            fn()

    def _raise_missing_service(self, service_name):
        raise UnknownServiceError(service_name)
