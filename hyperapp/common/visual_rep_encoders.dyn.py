from .interface import module as module_types
from .interface import resource as resource_types
from .visual_rep import RepNode, special_encoder_registry
from .module import Module


MODULE_NAME = 'visual_rep_encoders'


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        special_encoder_registry.register(module_types.requirement, self._encode_module_requirement)
        special_encoder_registry.register(module_types.module, self._encode_module_module)
        special_encoder_registry.register(resource_types.resource_id, self._encode_resouce_id)

    def _encode_module_requirement(self, requirement):
        return RepNode('requirement: %s' % ':'.join(value))

    def _encode_resouce_id(self, resource_id):
        return RepNode(encode_path(resource_id))

    def _encode_module_module(self, module):
        return RepNode('module: id=%s, package=%s, satisfies=%r' % (module.id, module.package, module.satisfies))
