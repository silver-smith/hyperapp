
class TreeDiff:

    @classmethod
    def insert(cls, path, item):
        return TreeDiffInsert(path, item)

    @classmethod
    def append(cls, path, item):
        return TreeDiffAppend(path, item)

    @classmethod
    def remove(cls, path):
        return TreeDiffRemove(path)

    @classmethod
    def modify(cls, path, item_diff):
        return TreeDiffModify(path, item_diff)


class TreeDiffInsert:

    def __init__(self, path, item):
        self.path = path
        self.item = item

    def __repr__(self):
        return f"<TreeDiffInsert: @#{self.path}: {self.item}>"


class TreeDiffRemove:

    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return f"<TreeDiffRemove: @#{self.path}>"


class TreeDiffAppend:

    def __init__(self, path, item):
        self.path = path
        self.item = item

    def __repr__(self):
        return f"<TreeDiffAppend: @#{self.path}: {self.item}>"


class TreeDiffModify:

    def __init__(self, path, item_diff):
        self.path = path
        self.item_diff = item_diff

    def __repr__(self):
        return f"<TreeDiffModify: @#{self.path}: {self.item_diff}>"
