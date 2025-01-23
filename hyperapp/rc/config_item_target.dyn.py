from .code.rc_target import Target


# Ready for testing: provider is found and all deps are completed.
class ConfigItemReadyTarget(Target):

    @staticmethod
    def target_name(service_name, key):
        return f'item-ready/{service_name}/{key}'

    def __init__(self, service_name, key, all_imports_known_tgt):
        self._service_name = service_name
        self._key = key
        self._all_imports_known_tgt = all_imports_known_tgt
        self._target_set = None
        self._completed = False
        self._provider_resource_tgt = None
        self._import_tgt = None

    @property
    def name(self):
        return self.target_name(self._service_name, self._key)

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        if self._provider_resource_tgt:
            return {self._import_tgt}
        else:
            return {self._all_imports_known_tgt}

    def update_status(self):
        if self._completed:
            return
        if self._provider_resource_tgt and self._provider_resource_tgt.completed:
            self._completed = True
        elif self._import_tgt and self._import_tgt.completed:
            self._completed = True

    @property
    def adopted_by(self):
        return self._target_set

    @property
    def provider_resource_tgt(self):
        return self._provider_resource_tgt

    def set_provider(self, resource_tgt):
        if self._provider_resource_tgt:
            # TODO: Add special case for feed factory:
            # method like add_provider and multiple constructors with comparison and merge methods.
            if self._provider_resource_tgt is not resource_tgt and self._service_name != 'feed_factory':
                raise RuntimeError(
                    f"Configuration item {self._service_name}/{self._key} is provided by two different modules:"
                    f" {self._provider_resource_tgt.module_name} and {resource_tgt.module_name}"
                    )
            return
        self._provider_resource_tgt = resource_tgt
        self._import_tgt = resource_tgt.import_tgt  # None for manual python module provider resource.
        self._target_set = resource_tgt.target_set
        self._target_set.adopt(self)
        # for test_target in self._unresolved_in_tests:
        #     resource_tgt.add_test(test_target, target_set)


# Tests passed, have enough info for construction.
class ConfigItemResolvedTarget(Target):

    @staticmethod
    def target_name(service_name, key):
        return f'item-resolved/{service_name}/{key}'

    def __init__(self, service_name, key, ready_tgt):
        self._service_name = service_name
        self._key = key
        self._ready_tgt = ready_tgt
        self._target_set = None
        self._completed = False
        self._provider_resource_tgt = None
        self._ctr = None
        self._custom_deps = set()

    @property
    def name(self):
        return self.target_name(self._service_name, self._key)

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        return {self._ready_tgt, *self._custom_deps}

    def update_status(self):
        if not self._ctr:
            return
        if not self._target_set:
            self._target_set = self._ready_tgt.adopted_by
            self._target_set.adopt(self)
        self._completed = all(target.completed for target in self.deps)

    def add_dep(self, target):
        self._custom_deps.add(target)

    @property
    def adopted_by(self):
        return self._target_set

    @property
    def provider_resource_tgt(self):
        return self._provider_resource_tgt

    @property
    def constructor(self):
        assert self._completed
        return self._ctr

    def resolve(self, ctr):
        self._ctr = ctr
        self._provider_resource_tgt = self._ready_tgt.provider_resource_tgt
        self.update_status()


# Configuration item is ready to use.
class ConfigItemCompleteTarget(Target):

    @staticmethod
    def target_name(service_name, key):
        return f'item-complete/{service_name}/{key}'

    def __init__(self, service_name, key, resolved_tgt, service_cfg_item_complete_tgt):
        self._service_name = service_name
        self._key = key
        self._resolved_tgt = resolved_tgt
        self._service_cfg_item_complete_tgt = service_cfg_item_complete_tgt
        self._target_set = None
        self._completed = False
        self._provider_resource_tgt = None
        self._ctr = None

    @property
    def name(self):
        return self.target_name(self._service_name, self._key)

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        deps = {self._resolved_tgt}
        if self._service_cfg_item_complete_tgt:
            deps.add(self._service_cfg_item_complete_tgt)
        if self._provider_resource_tgt:
            deps.add(self._provider_resource_tgt)
        return deps

    def update_status(self):
        if self._completed:
            return
        if not self._provider_resource_tgt:
            if self._resolved_tgt.completed:
                self._provider_resource_tgt = self._resolved_tgt.provider_resource_tgt
                self._ctr = self._resolved_tgt.constructor
                assert self._provider_resource_tgt
            else:
                return
        if not self._provider_resource_tgt.completed:
            return
        if self._service_cfg_item_complete_tgt and not self._service_cfg_item_complete_tgt.completed:
            return
        if not self._target_set:
            self._target_set = self._resolved_tgt.adopted_by
            self._target_set.adopt(self)
        self._completed = True

    @property
    def provider_resource_tgt(self):
        assert self._completed
        return self._provider_resource_tgt

    @property
    def constructor(self):
        assert self._completed
        return self._ctr

    @property
    def resource(self):
        assert self._completed
        return self._provider_resource_tgt.get_resource_component(self._ctr)
