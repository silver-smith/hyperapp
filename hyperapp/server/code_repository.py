import os.path
import simpleyaml as yaml
from ..common.interface.code_repository import (
    tModule,
    code_repository_iface,
    )
from . import module as module_mod
from .object import Object


MODULE_NAME = 'code_repository'
DYNAMIC_MODULES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dynamic_modules'))
DYNAMIC_MODULE_INFO_EXT = '.module.yaml'


class CodeRepository(Object):

    iface = code_repository_iface
    class_name = 'code_repository'

    @classmethod
    def get_path( cls ):
        return module.make_path(cls.class_name)

    def __init__( self ):
        Object.__init__(self)
        self._id2module = {}           # module id -> tModule
        self._requirement2module = {}  # (registry, key) -> tModule
        self._load_dynamic_modules()

    def resolve( self, path ):
        path.check_empty()
        return self

    def process_request( self, request ):
        if request.command_id == 'get_modules':
            return self.run_command_get_modules(request)
        if request.command_id == 'get_required_modules':
            return self.run_command_get_required_modules(request)
        return Object.process_request(self, request)

    def run_command_get_modules( self, request ):
        print 'run_command_get_modules', request.params.module_ids
        return request.make_response_result(
            modules=self.get_modules(request.params.module_ids))

    def run_command_get_required_modules( self, request ):
        print 'run_command_get_required_modules', request.params.requirements
        return request.make_response_result(
            modules=self.get_required_modules(request.params.requirements))

    def get_modules( self, module_ids ):
        return [self._id2module[id] for id in module_ids]

    def get_required_modules( self, requirements ):
        modules = []
        for registry, key in requirements:
            module = self._requirement2module.get((registry, key))
            if module:
                modules.append(module)
            else:
                print 'Unknown requirement: %s/%s' % (registry, key)  # May be statically loaded, ignore
        return modules

    def _load_dynamic_modules( self ):
        for fname in os.listdir(DYNAMIC_MODULES_DIR):
            if fname.endswith(DYNAMIC_MODULE_INFO_EXT):
                self._load_dynamic_module(os.path.join(DYNAMIC_MODULES_DIR, fname))

    def _load_dynamic_module( self, info_path ):
        with open(info_path) as f:
            info = yaml.load(f.read())
        print 'loaded module info:', info
        source_path = os.path.abspath(os.path.join(DYNAMIC_MODULES_DIR, info['source_path']))
        satisfies = [path.split('/') for path in info['satisfies']]
        module = self._load_module(info['id'], info['package'], satisfies, source_path)
        for registry, key in satisfies:
            self._id2module[module.id] = module
            self._requirement2module[(registry, key)] = module

    def _load_module( self, id, package, satisfies, fpath ):
        fpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', fpath))
        with open(fpath) as f:
            source = f.read()
        return tModule(id=id, package=package, deps=[], satisfies=satisfies, source=source, fpath=fpath)


class CodeRepositoryModule(module_mod.Module):

    def __init__( self ):
        module_mod.Module.__init__(self, MODULE_NAME)

    def resolve( self, iface, path ):
        objname = path.pop_str()
        if objname == CodeRepository.class_name:
            return code_repository.resolve(path)
        path.raise_not_found()


code_repository = CodeRepository()
module = CodeRepositoryModule()
