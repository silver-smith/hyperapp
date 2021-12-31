import logging
import yaml

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ResourceModule:

    def __init__(self, mosaic, resource_type_registry, resource_module_registry, name, path):
        self._mosaic = mosaic
        self._resource_type_registry = resource_type_registry
        self._resource_module_registry = resource_module_registry
        self._name = name
        self._path = path
        self._definitions = None
        self._import_list = None

    def __contains__(self, var_name):
        return var_name in self._definitions

    def make(self, var_name):
        if self._definitions is None:
            self._load()
        try:
            definition = self._definitions[var_name]
        except KeyError:
            raise RuntimeError(f"Resource module {self._name!r}: Unknown resource: {var_name!r}")
        factory = self._resource_type_registry[definition['type']]
        piece = factory(definition, self._resolve_name)
        log.info("%s: Loaded resource %r: %s", self._name, var_name, piece)
        return piece

    def _resolve_name(self, name):
        if name in self._import_list:
            module_name, var_name = name.rsplit('.', 1)
            module = self._resource_module_registry[module_name]
            piece = module.make(var_name)
        else:
            piece = self.make(name)
        return self._mosaic.put(piece)
        
    def _load(self):
        log.info("Loading resource module %s: %s", self._name, self._path)
        definitions = yaml.safe_load(self._path.read_text())
        import_list = definitions.get('import', [])
        for name in import_list:
            module_name, var_name = name.rsplit('.', 1)
            try:
                module = self._resource_module_registry[module_name]
            except KeyError:
                raise RuntimeError(f"{self._name}: Importing {var_name} from unknown module: {module_name}")
            if var_name not in module:
                raise RuntimeError(f"{self._name}: Module {module_name} does not have {var_name!r}")
        self._definitions = {
            key: value for key, value in definitions.items()
            if key != 'import'
            }
        self._import_list = import_list


def load_resource_modules(mosaic, resource_type_registry, dir_list):
    ext = '.resources.yaml'
    registry = {}
    for root_dir in dir_list:
        for path in root_dir.rglob(f'*{ext}'):
            rpath = str(path.relative_to(root_dir))
            name = rpath[:-len(ext)].replace('/', '.')
            log.info("Resource module: %r", name)
            registry[name] = ResourceModule(mosaic, resource_type_registry, registry, name, path)
    return registry


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_module_registry = load_resource_modules(
            services.mosaic, services.resource_type_registry, services.module_dir_list)
