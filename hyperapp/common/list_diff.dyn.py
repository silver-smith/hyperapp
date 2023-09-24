

class ListDiff:

    @classmethod
    def insert(cls, idx, item):
        return ListDiffInsert(idx, item)


class ListDiffInsert:

    def __init__(self, idx, item):
        self.idx = idx
        self.item = item
