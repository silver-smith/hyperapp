from .code.service_target import ServiceCompleteReq


class RequirementFactory:

    def import_to_htype(self, import_path):
        pass

    def import_to_service(self, import_path):
        if len(import_path) == 1:
            return
        service_name = import_path[1]
        return ServiceCompleteReq(service_name)

    def import_to_code(self, import_path):
        pass

    def import_to_tested_service(self, import_path):
        pass

    def import_to_tested_code(self, import_path):
        pass

    def ignore_import(self, import_path):
        pass

    prefix_to_factory = {
        ('htypes',): import_to_htype,
        ('services',): import_to_service,
        ('code',): import_to_code,
        ('tested', 'services'): import_to_tested_service,
        ('tested', 'code'): import_to_tested_code,
        ('tested',): ignore_import,
        }

    def requirement_from_import(self, import_path):
        for prefix, factory in self.prefix_to_factory.items():
            if import_path[:len(prefix)] == prefix:
                return factory(self, import_path)
        raise RuntimeError(f"Unknown import kind: {'.'.join(import_path)!r}")
