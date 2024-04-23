
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


class TreeDiffReplace:

    def __init__(self, path, item):
        self.path = path
        self.item = item

    def __repr__(self):
        return f"<TreeDiffReplace: @#{self.path}: {self.item}>"


class TreeDiffModify:

    def __init__(self, path, item_diff):
        self.path = path
        self.item_diff = item_diff

    def __repr__(self):
        return f"<TreeDiffModify: @#{self.path}: {self.item_diff}>"


class TreeDiff:
    Insert = TreeDiffInsert
    Append = TreeDiffAppend
    Replace = TreeDiffReplace
    Remove = TreeDiffRemove
    Modify = TreeDiffModify
