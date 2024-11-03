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
        self._completed = False
        self._provider_resource_tgt = None
        self._import_alias_tgt = None

    @property
    def name(self):
        return self.target_name(self._service_name, self._key)

    @property
    def completed(self):
        return self._completed

    @property
    def deps(self):
        if self._import_alias_tgt:
            return {self._import_alias_tgt}
        else:
            return {self._all_imports_known_tgt}

    def update_status(self):
        if self._completed:
            return
        if self._provider_resource_tgt and self._provider_resource_tgt.completed:
            self._completed = True
        elif self._import_alias_tgt and self._import_alias_tgt.completed:
            self._completed = True

    @property
    def provider_resource_tgt(self):
        return self._provider_resource_tgt

    def set_provider(self, resource_tgt, target_set):
        self._provider_resource_tgt = resource_tgt
        self._import_alias_tgt = resource_tgt.import_alias_tgt
        # for test_target in self._unresolved_in_tests:
        #     resource_tgt.add_test(test_target, target_set)
        self.update_status()


# Tests passed, have enough info for construction.
class ConfigItemResolvedTarget(Target):

    @staticmethod
    def target_name(service_name, key):
        return f'item-resolved/{service_name}/{key}'

    def __init__(self, service_name, key, ready_tgt):
        self._service_name = service_name
        self._key = key
        self._ready_tgt = ready_tgt
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
        return {self._ready_tgt}

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
        self._completed = True


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
        if not self._provider_resource_tgt and self._resolved_tgt.completed:
            self._provider_resource_tgt = self._resolved_tgt.provider_resource_tgt
            self._ctr = self._resolved_tgt.constructor
        if not self._provider_resource_tgt or not self._provider_resource_tgt.completed:
            return
        if self._service_cfg_item_complete_tgt and not self._service_cfg_item_complete_tgt.completed:
            return
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
