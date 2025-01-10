from collections import namedtuple

from hyperapp.boot.htypes import (
    TPrimitive,
    TOptional,
    TList,
    TRecord,
    TException,
    ref_t,
    )

from .services import deduce_t


class NoPicker:

  def pick_refs(self, value):
      return []


class OptPicker:

    def __init__(self, base_picker):
        self._base_picker = base_picker

    def pick_refs(self, value):
        if value is not None:
            yield from self._base_picker.pick_refs(value)


class ListPicker:

    def __init__(self, element_picker):
        self._element_picker = element_picker

    def pick_refs(self, value):
        for elt in value:
            yield from self._element_picker.pick_refs(elt)


class RecordPicker:

    def __init__(self, fields):
        self._fields = fields  # name -> picker

    def pick_refs(self, value):
        for name, picker in self._fields.items():
            yield from picker.pick_refs(getattr(value, name))


class RefPicker:

    def pick_refs(self, value):
        yield value


def _type_to_picker(t):
    if t is ref_t:
        return RefPicker()
    if isinstance(t, TPrimitive):
        return NoPicker()
    tt = type(t)
    if tt is TOptional:
        return OptPicker(_type_to_picker(t.base_t))
    if tt is TList:
        return ListPicker(_type_to_picker(t.element_t))
    if tt is TRecord or tt is TException:
        return RecordPicker({
            name: _type_to_picker(field_t)
            for name, field_t in t.fields.items()
            })


RefPickerCache = namedtuple('RefPickerCache', 't_to_picker value_to_refs')


def ref_picker_cache():
    return RefPickerCache({}, {})


def pick_refs(ref_picker_cache, value, t=None):
    try:
        return ref_picker_cache.value_to_refs[value]
    except KeyError:
        pass
    if t is None:
        t = deduce_t(value)
    try:
        picker = ref_picker_cache.t_to_picker[t]
    except KeyError:
        picker = ref_picker_cache.t_to_picker[t] = _type_to_picker(t)
    refs = set(picker.pick_refs(value))
    ref_picker_cache.value_to_refs[value] = refs
    return refs
