from .visual_rep import RepNode, special_encoder_registry
from .module import Module
from . import htypes


MODULE_NAME = 'visual_rep_encoders'


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        special_encoder_registry.register(htypes.module.requirement, self._encode_module_requirement)
        special_encoder_registry.register(htypes.module.module, self._encode_module_module)
        special_encoder_registry.register(htypes.resource.resource_id, self._encode_resouce_id)

    def _encode_module_requirement(self, requirement):
        return RepNode('requirement: %s' % ':'.join(value))

    def _encode_resouce_id(self, resource_id):
        return RepNode(encode_path(resource_id))

    def _encode_module_module(self, module):
        return RepNode('module: id=%s, package=%s, satisfies=%r' % (module.id, module.package, module.satisfies))
