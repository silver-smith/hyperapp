from collections import namedtuple


ResourcePath = namedtuple('ResourcePath', 'name path')


class ResourceDir:

    def __init__(self, root, sub_dirs=None):
        self.root = root
        self._sub_dirs = [
            d.relative_to(root) if d.is_absolute() else d
            for d in sub_dirs or []
            ]

    def enum(self):
        if self._sub_dirs:
            for dir in self._sub_dirs:
                yield from self._enum(self.root / dir)
        else:
            yield from self._enum(self.root)

    def _enum(self, dir):
        ext = '.resources.yaml'
        for path in dir.rglob(f'*{ext}'):
            if 'test' in path.relative_to(self.root).parts:
                continue  # Skip test subdirectories.
            rpath = str(path.relative_to(self.root))
            name = rpath[:-len(ext)].replace('/', '.')
            yield ResourcePath(name, path)
