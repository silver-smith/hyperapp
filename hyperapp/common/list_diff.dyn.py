

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
