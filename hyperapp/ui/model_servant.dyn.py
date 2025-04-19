import logging

from .code.mark import mark

log = logging.getLogger(__name__)


class ModelServant:

    def __init__(self, model):
        self._model = model
        self._key_field = None
        self._key_field_t = None
        self._servant_fn = None

    @property
    def fn(self):
        assert self._servant_fn  # set_servant_fn was not yet called: Model is not yet populated.
        return self._servant_fn

    @property
    def key_field(self):
        assert self._servant_fn  # set_servant_fn was not yet called: Model is not yet populated.
        return self._key_field

    @property
    def key_field_t(self):
        assert self._servant_fn  # set_servant_fn was not yet called: Model is not yet populated.
        return self._key_field_t

    def set_servant_fn(self, key_field, key_field_t, fn):
        log.info("Got model servant: %s -> [%s: %s] %s", self._model, key_field, key_field_t, fn)
        self._key_field = key_field
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
