

class ListDiff:

    @classmethod
    def insert(cls, idx, item):
        return ListDiffInsert(idx, item)


class ListDiffInsert:

    def __init__(self, idx, item):
        self.idx = idx
        self.item = item

    def __repr__(self):
        return f"<ListDiffInsert: @#{self.idx}: {self.item}>"

    def apply(self, value):
        assert type(value) in {list, tuple}, repr(value)
        result = [*value]
        result.insert(self.idx, self.item)
        return result


class ListDiffModify:

    def __init__(self, idx, item_diff):
        self.idx = idx
        self.item_diff = item_diff

    def __repr__(self):
        return f"<ListDiffModify: @#{self.idx}: {self.item_diff}>"

    def apply(self, value):
        assert type(value) in {list, tuple}, repr(value)
        return [
            *value[:self.idx],
            self.item_diff.apply(value[self.idx]),
            *value[self.idx + 1:],
            ]
