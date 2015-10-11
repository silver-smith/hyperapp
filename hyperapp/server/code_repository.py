import os.path
from ..common.interface.code_repository import (
    ModuleDep,
    Module,
    code_repository_iface,
    )
from . import module as module_mod
from .object import Object


MODULE_NAME = 'code_repository'



class CodeRepository(Object):

    iface = code_repository_iface
    class_name = 'code_repository'

    @classmethod
    def get_path( cls ):
        return module.make_path(cls.class_name)

    def resolve( self, path ):
        path.check_empty()
        return self

    def process_request( self, request ):
        if request.command_id == 'get_required_modules':
            return self.run_command_get_required_modules(request)
        return Object.process_request(self, request)

    def run_command_get_required_modules( self, request ):
        print 'run_command_get_required_modules', request.params.requirements
        test_list_iface_module = self._load_module(
            '0df259a7-ca1c-43d5-b9fa-f787a7271db9', 'hyperapp.common.interface', 'common/interface/test_list.py')
        proxy_text_module = self._load_module('5142abef-6cb4-4093-8e5e-d6443deffb79', 'hyperapp.client', 'client/proxy_text_object.py')
        form_module = self._load_module('7e947453-84f3-44e9-961c-3e18fcdc37f0', 'hyperapp.client', 'client/form.py')
        return request.make_response_result(
            modules=[form_module, proxy_text_module, test_list_iface_module])

    def _load_module( self, id, package, fpath ):
        fpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', fpath))
        with open(fpath) as f:
            source = f.read()
        return Module(id=id, package=package, deps=[], source=source, fpath=fpath)


class CodeRepositoryModule(module_mod.Module):

    def __init__( self ):
        module_mod.Module.__init__(self, MODULE_NAME)

    def resolve( self, path ):
        objname = path.pop_str()
        if objname == CodeRepository.class_name:
            return code_repository.resolve(path)
        path.raise_not_found()


code_repository = CodeRepository()
module = CodeRepositoryModule()
