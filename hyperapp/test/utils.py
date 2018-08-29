import logging

from hyperapp.common.htypes.packet_coders import packet_coders

log = logging.getLogger(__name__)


BUNDLE_ENCODING = 'json'


def log_exceptions_wrapper(fn):
    def inner(*args, **kw):
        try:
            return fn(*args, **kw)
        except:
            log.exception('Exception in %s:', fn.__name__)
            raise
    return inner

def log_exceptions(name, bases, attrs):
    new_attrs = {}
    for name, value in attrs.items():
        if callable(value):
            new_attrs[name] = log_exceptions_wrapper(value)
        else:
            new_attrs[name] = value
    return type(name, bases, new_attrs)


def encode_bundle(services, bundle):
    return packet_coders.encode(BUNDLE_ENCODING, bundle)

def decode_bundle(services, encoded_bundle):
    return packet_coders.decode(BUNDLE_ENCODING, encoded_bundle, services.types.hyper_ref.bundle)
