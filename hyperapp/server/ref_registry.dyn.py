import logging

from ..common.interface import hyper_ref as href_types
from ..common.ref import make_referred, make_ref
from .module import Module

log = logging.getLogger(__name__)


MODULE_NAME = 'ref_registry'


class RefRegistry(object):
    pass


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        services.ref_registry = RefRegistry()
