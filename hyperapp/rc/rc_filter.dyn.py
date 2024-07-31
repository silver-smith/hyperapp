
class Filter:

    def __init__(self, target_set, target_names):
        self._target_set = target_set
        self._target_names = set(target_names)
        self._wanted_names = set()
        self.update_deps()

    def included(self, target):
        if not self._target_names:
            return True
        return target.name in self._wanted_names

    def update_deps(self):
        targets = set()
        name_set = set(self._target_names)
        while name_set:
            name = name_set.pop()
            try:
                tgt = self._target_set[name]
            except KeyError:
                hints = set(self._get_hints(name))
                if not hints:
                    raise RuntimeError(f"Unknown target: {name!r}")
                name_set |= hints
                self._wanted_names.add(name)
            else:
                targets.add(tgt)
        while targets:
            next_targets = set()
            for tgt in targets:
                self._wanted_names.add(tgt.name)
                for dep in tgt.deps:
                    next_targets.add(dep)
            targets = next_targets

    @staticmethod
    def _get_hints(target_name):
        parts = target_name.split('/')
        if parts[0] == 'test':
            yield f'import/{parts[1]}'
        if parts[0] == 'import' and len(parts) == 3:
            idx = int(parts[2])
            if idx > 1:
                for i in range(1, idx):
                    yield '/'.join([*parts[:2], str(i)])
        if parts[0] == 'test' and len(parts) == 4:
            idx = int(parts[3])
            if idx > 1:
                for i in range(1, idx):
                    yield '/'.join([*parts[:3], str(i)])
        if parts[0] == 'resource':
            yield f'import/{parts[1]}'
