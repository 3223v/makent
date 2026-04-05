import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ToolExecutionResult:
    tool_name: str
    tool_call_id: Optional[str]
    success: bool
    content: str
    raw: Any = None


class ToolExecutor:
    def __init__(self, registry):
        self.registry = registry

    def schemas(self):
        return self.registry.schemas()

    def execute(self, tool_call):
        tool = self.registry.get(tool_call.name)

        if not tool:
            return ToolExecutionResult(
                tool_name=tool_call.name,
                tool_call_id=tool_call.id,
                success=False,
                content=f"tool {tool_call.name} not found"
            )

        try:
            raw_result = tool.func(**tool_call.arguments)
            return ToolExecutionResult(
                tool_name=tool_call.name,
                tool_call_id=tool_call.id,
                success=True,
                content=self._stringify(raw_result),
                raw=raw_result
            )
        except Exception as exc:
            return ToolExecutionResult(
                tool_name=tool_call.name,
                tool_call_id=tool_call.id,
                success=False,
                content=f"error: {exc}"
            )

    def _stringify(self, value: Any) -> str:
        if isinstance(value, str):
            return value

        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except TypeError:
            return str(value)
