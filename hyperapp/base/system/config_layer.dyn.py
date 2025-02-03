import itertools
from functools import cached_property

from hyperapp.boot.htypes import TPrimitive, TRecord, tString
from hyperapp.boot.project import RESOURCE_EXT

from . import htypes
from .services import (
    code_registry_ctr,
    deduce_t,
    mosaic,
    resource_module_factory,
    web,
    )


# class SimpleConfigLayer:

#     def __init__(self, config):
#         self._config = config

#     @property
#     def config(self):
#         return self._config


class ConfigLayer:

    def __init__(self, system, config_ctl):
        self._system = system
        self._config_ctl = config_ctl

    def _data_to_config(self, config_piece):
        service_to_config_piece = {
            rec.service: web.summon(rec.config)
            for rec in config_piece.services
            }
        ordered_services = sorted(service_to_config_piece, key=self._system.service_config_order)
        service_to_config = {}
        for service_name in ordered_services:
            piece = service_to_config_piece.get(service_name)
            if not piece:
                continue
            ctl = self._config_ctl[service_name]
            config = ctl.from_data(piece)
            if service_name in {'config_ctl_creg', 'cfg_item_creg'}:
                # Subsequent ctl.from_data calls may already use it.
                self._system.update_service_own_config(service_name, config)
            if service_name == 'system':
                # Subsequent ctl.from_data calls may already use it.
                self._system.update_config_ctl(config)
            service_to_config[service_name] = config
        return service_to_config


class StaticConfigLayer(ConfigLayer):

    def __init__(self, system, config_ctl, config_piece):
        super().__init__(system, config_ctl)
        self._config_piece = config_piece

    @property
    def config(self):
        return self._data_to_config(self._config_piece)

    def set(self, service_name, key, value):
        raise NotImplementedError()


class ProjectConfigLayer(ConfigLayer):

    def __init__(self, system, config_ctl, project):
        super().__init__(system, config_ctl)
        self._project = project
        # Non-builtin services are not yet available when layer is created.
        self._name_gen = None
        self._pick_refs = None
        if project.path.is_dir():
            self._config_module_name = f'{project.name}.config'
            self._module_path = project.path / f'config{RESOURCE_EXT}'
            self._resource_dir = project.path
        else:
            self._config_module_name = self._project.name
            self._module_path = project.path
            self._resource_dir = project.path.parent
        self._module = self._project.get_module(self._config_module_name)

    @cached_property
    def config(self):
        if not self._module:
            return {}
        try:
            config_piece = self._module['config']
        except KeyError:
            return {}
        return self._data_to_config(config_piece)

    def set(self, service_name, key, value):
        try:
            service_config = self.config[service_name]
        except KeyError:
            service_config = self._config_ctl[service_name].empty_config_template()
            self.config[service_name] = service_config
        service_config[key] = value
        self._save()
        self._system.invalidate_config_cache()

    def _save(self):
        # We should remove not only old values from mapping,
        # but also now-unused elements they reference.
        # Thus, construct it from afresh every time.
        if self._module:
            self._module.clear()
        else:
            self._module = resource_module_factory(
                self._project, self._config_module_name, self._module_path, resource_dir=self._resource_dir, load_from_file=False)
        if not self._name_gen:
            self._name_gen = ResourceNameGenerator(self._system['resource_name_creg'], self._project, self._module)
        if not self._pick_refs:
            self._pick_refs = self._system['pick_refs']
        service_to_piece = {}
        for service_name, config in self.config.items():
            ctl = self._config_ctl[service_name]
            piece = ctl.to_data(config)
            service_to_piece[service_name] = piece
            self._ensure_refs_stored(piece)
            self._module[f'{service_name}.config'] = piece
        config_piece = htypes.system.system_config(tuple(
            htypes.system.service_config(
                service=service_name,
                config=mosaic.put(piece),
                )
            for service_name, piece in service_to_piece.items()
            ))
        self._module['config'] = config_piece
        self._module.save()

    def _ensure_refs_stored(self, piece, t=None):
        if t is None:
            t = deduce_t(piece)
        for ref in self._pick_refs(piece, t):
            elt_piece, elt_t = web.summon_with_t(ref)
            self._ensure_stored(elt_piece, elt_t)

    def _ensure_stored(self, piece, t):
        if self._project.has_piece(piece):
            return
        self._ensure_refs_stored(piece, t)
        name = self._make_name(piece, t)
        self._module[name] = piece

    def _make_name(self, piece, t):
        tried_names = []
        for name in self._iter_names(piece, t):
            if name not in self._module:
                return name
            tried_names.append(name)
        raise RuntimeError(f"All names ({', '.join(tried_names)}) for piece {piece!r} are already in use")

    def _iter_names(self, piece, t):
        stem, require_index = self._name_gen.make_stem_and_index_requirement(piece, t)
        if not require_index:
            yield stem
            if isinstance(t, TRecord):
                yield f'{t.module_name}.{stem}'
            return
        for idx in itertools.count(1):
            yield f'{stem}_{idx}'


class ResourceNameGenerator:

    def __init__(self, resource_name_creg, project, resource_module):
        self._resource_name_creg = resource_name_creg
        self._project = project
        self._module = resource_module

    def assigned_name(self, piece):
        module_name, name = self._project.reverse_resolve(piece)
        if module_name == self._module.name:
            return name
        return f'{module_name}:{name}'

    def make_stem(self, piece, t=None):
        if t is None:
            t = deduce_t(piece)
        stem, require_index = self.make_stem_and_index_requirement(piece, t)
        return stem

    def make_stem_and_index_requirement(self, piece, t):
        try:
            stem = self._resource_name_creg.animate(piece, self)
        except KeyError:
            pass
        else:
            if stem:
                return (stem, False)
        stem = self._make_default_stem(piece, t)
        require_index = self._require_index(piece, t, stem)
        return (stem, require_index)

    def _make_default_stem(self, piece, t):
        if isinstance(t, TPrimitive):
            return t.name
        else:
            assert isinstance(t, TRecord)
            if t.name in {'view', 'layout', 'state', 'adapter'}:
                mnl = t.module_name.split('.')
                return f'{mnl[-1]}_{t.name}'
            return t.name

    def _require_index(self, piece, t, stem):
        if not isinstance(t, TRecord):
            return True
        if t.name == stem:
            # Custom type name is added to resource module by type name.
            # If it matches value name, index suffix should be added to avoid name clash.
            return True
        return bool(t.fields)


def resource_name_creg(config):
    return code_registry_ctr('resource_name_creg', config)
