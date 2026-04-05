try:
    from .base import ToolProvider
except ImportError:
    from base import ToolProvider


class McpToolProvider(ToolProvider):
    name = "mcp"

    def __init__(self, mcp_dir: str, server_names=None):
        self.mcp_dir = mcp_dir
        self.server_names = list(server_names or [])

    def load_into(self, registry):
        registry.load_from_mcp_modules(self.mcp_dir)
        return registry
