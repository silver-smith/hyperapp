
def replace(container, idx, item):
    assert type(container) in {list, tuple}, repr(container)
    return [
        *container[:idx],
        item,
        *container[idx + 1:],
        ]


class ListDiffInsertIdx:

    def __init__(self, idx, item):
        self.idx = idx
        self.item = item

    def __repr__(self):
        return f"<ListDiffInsertIdx: @#{self.idx}: {self.item}>"

    def apply(self, value):
        assert type(value) in {list, tuple}, repr(value)
        return self.insert(value, self.item)

    def insert(self, container, item):
        assert type(container) in {list, tuple}, repr(container)
        return [
            *container[:self.idx],
            item,
            *container[self.idx:],
            ]


class ListDiffInsertKey:

    def __init__(self, key, item):
        self.key = key
        self.item = item

    def __repr__(self):
        return f"<ListDiffInsertKey: @#{self.key}: {self.item}>"


class ListDiffRemoveIdx:

    def __init__(self, idx):
        self.idx = idx

    def __repr__(self):
        return f"<ListDiffRemoveIdx: @#{self.idx}>"

    def apply(self, value):
        assert type(value) in {list, tuple}, repr(value)
        return self.remove(value)

    def remove(self, container):
        assert type(container) in {list, tuple}, repr(container)
        return [
            *container[:self.idx],
            *container[self.idx + 1:],
            ]


class ListDiffRemoveKey:

    def __init__(self, key):
        self.key = key

    def __repr__(self):
        return f"<ListDiffRemoveKey: @#{self.key}>"


class ListDiffAppend:

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return f"<ListDiffAppend: {self.item}>"


class ListDiffReplaceIdx:

    def __init__(self, idx, item):
        self.idx = idx
        self.item = item

    def __repr__(self):
        return f"<ListDiffReplaceIdx: @#{self.idx}: {self.item}>"

    def replace(self, container, item):
        return replace(container, self.idx, item)


class ListDiffReplaceKey:

    def __init__(self, key, item):
        self.key = key
        self.item = item

    def __repr__(self):
        return f"<ListDiffReplaceKey: @#{self.key}: {self.item}>"


class ListDiffModifyIdx:

    def __init__(self, idx, item_diff):
        self.idx = idx
        self.item_diff = item_diff

    def __repr__(self):
        return f"<ListDiffModifyIdx: @#{self.idx}: {self.item_diff}>"

    def replace(self, container, item):
        return replace(container, self.idx, item)


class ListDiffModifyKey:

    def __init__(self, key, item_diff):
        self.key = key
        self.item_diff = item_diff

    def __repr__(self):
        return f"<ListDiffModifyKey: @#{self.key}: {self.item_diff}>"


class IndexListDiff:
    Insert = ListDiffInsertIdx
    Append = ListDiffAppend
    Remove = ListDiffRemoveIdx
    Replace = ListDiffReplaceIdx
    Modify = ListDiffModifyIdx


class KeyListDiff:
    Insert = ListDiffInsertKey
    Append = ListDiffAppend
    Remove = ListDiffRemoveKey
    Replace = ListDiffReplaceKey
    Modify = ListDiffModifyKey
