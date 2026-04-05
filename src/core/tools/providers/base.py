class ToolProvider:
    name = "provider"

    def load_into(self, registry):
        raise NotImplementedError
