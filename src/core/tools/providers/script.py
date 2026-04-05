try:
    from .base import ToolProvider
except ImportError:
    from base import ToolProvider


class ScriptToolProvider(ToolProvider):
    name = "script"

    def __init__(self, script_dir: str):
        self.script_dir = script_dir

    def load_into(self, registry):
        registry.load_from_scripts(self.script_dir)
        return registry
