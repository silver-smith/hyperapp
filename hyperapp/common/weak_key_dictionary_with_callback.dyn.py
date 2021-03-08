import weakref


# calls 'on_remove' callback every time an item is removed
# WARNING: uses undocumented WeakKeyDictionary implementation details
class WeakKeyDictionaryWithCallback(weakref.WeakKeyDictionary):

    def __init__(self, on_remove, data=None):
        super().__init__(data)
        self._orig_remove = self._remove
        self._on_remove = on_remove

        def remove(item, self_ref=weakref.ref(self)):
            self = self_ref()
            if self is None: return
            self._orig_remove(item)
            self._on_remove()

        self._remove = remove
