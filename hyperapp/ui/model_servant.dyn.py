import logging

from .code.mark import mark

log = logging.getLogger(__name__)


class ModelServant:

    def __init__(self, model):
        self._model = model
        self._key_field_t = None
        self._servant_fn = None

    def set_servant_fn(self, key_field_t, fn):
        log.info("Got model servant: %s -> [%s] %s", self._model, key_field_t, fn)
        self._key_field_t = key_field_t
        self._servant_fn = fn


@mark.service
def model_to_servant_dict():
    return {}


@mark.service
def model_servant(model_to_servant_dict, model):
    try:
        return model_to_servant_dict[model]
    except KeyError:
        pass
    servant = ModelServant(model)
    model_to_servant_dict[model] = servant
    return servant
