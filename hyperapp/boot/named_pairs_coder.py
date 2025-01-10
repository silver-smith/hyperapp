from hyperapp.boot.htypes import TList, TRecord, tString


def is_named_pair_list_t(t):
    return (
        isinstance(t, TList)
        and isinstance(t.element_t, TRecord)
        and len(t.element_t.fields) == 2
        and list(t.element_t.fields.values())[0] is tString
        )
