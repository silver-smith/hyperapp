
class Filter:

    def __init__(self, target_set, target_names):
        self._target_set = target_set
        self._target_names = target_names
        self._wanted_targets = set()
        self._pick_deps()

    def included(self, target):
        if not self._target_names:
            return True
        return target in self._wanted_targets

    def _pick_deps(self):
        targets = set()
        for name in self._target_names:
            try:
                tgt = self._target_set[name]
            except KeyError:
                raise RuntimeError(f"Unknown target: {name!r}")
            targets.add(tgt)
        while targets:
            next_targets = set()
            for tgt in targets:
                self._wanted_targets.add(tgt)
                for dep in tgt.deps:
                    self._wanted_targets.add(dep)
                    next_targets.add(dep)
            targets = next_targets
