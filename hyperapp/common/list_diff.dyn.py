
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
        return f"<ListDiffInsert: @#{self.idx}: {self.item}>"

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


class ListDiffRemoveIdx:

    def __init__(self, idx):
        self.idx = idx

    def __repr__(self):
        return f"<ListDiffRemove: @#{self.idx}>"

    def apply(self, value):
        assert type(value) in {list, tuple}, repr(value)
        return self.remove(value)

    def remove(self, container):
        assert type(container) in {list, tuple}, repr(container)
        return [
            *container[:self.idx],
            *container[self.idx + 1:],
            ]


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
        return f"<ListDiffReplace: @#{self.idx}: {self.item}>"

    def replace(self, container, item):
        return replace(container, self.idx, item)


class ListDiffModifyIdx:

    def __init__(self, idx, item_diff):
        self.idx = idx
        self.item_diff = item_diff

    def __repr__(self):
        return f"<ListDiffModify: @#{self.idx}: {self.item_diff}>"

    def replace(self, container, item):
        return replace(container, self.idx, item)


class IndexListDiff:
    Insert = ListDiffInsertIdx
    Append = ListDiffAppend
    Remove = ListDiffRemoveIdx
    Replace = ListDiffReplaceIdx
    Modify = ListDiffModifyIdx
