import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentState:
    max_steps: int = 5
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_history: List[Dict[str, Any]] = field(default_factory=list)
    step: int = 0
    stop_reason: Optional[str] = None
    final_output: Optional[str] = None

    def set_system_prompt(self, content: str):
        message = {"role": "system", "content": content}

        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0] = message
        else:
            self.messages.insert(0, message)

    def add_message(self, role: str, content: Any, **extra):
        message = {"role": role, "content": content}
        message.update({key: value for key, value in extra.items() if value is not None})
        self.messages.append(message)
        return message

    def add_user_message(self, content: str):
        return self.add_message("user", content)

    def add_assistant_message(self, content: Optional[str] = None, tool_calls=None, raw_message: Optional[Dict[str, Any]] = None):
        if raw_message:
            message = dict(raw_message)
            message.setdefault("role", "assistant")
            if "content" not in message:
                message["content"] = content
            self.messages.append(message)
            return message

        message = {"role": "assistant", "content": content}

        if tool_calls:
            message["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments, ensure_ascii=False)
                    }
                }
                for call in tool_calls
            ]

        self.messages.append(message)
        return message

    def add_tool_result(
        self,
        tool_name: str,
        content: str,
        tool_call_id: Optional[str] = None,
        success: bool = True,
        raw: Any = None
    ):
        self.tool_history.append(
            {
                "step": self.step,
                "tool_name": tool_name,
                "tool_call_id": tool_call_id,
                "success": success,
                "content": content,
                "raw": raw
            }
        )

        return self.add_message(
            "tool",
            content,
            name=tool_name,
            tool_call_id=tool_call_id or tool_name
        )

    def mark_finished(self, output: str, reason: str):
        self.final_output = output
        self.stop_reason = reason

    def snapshot(self):
        return {
            "step": self.step,
            "max_steps": self.max_steps,
            "stop_reason": self.stop_reason,
            "final_output": self.final_output,
            "context": self.context,
            "metadata": self.metadata,
            "tool_history": self.tool_history,
            "messages": self.messages
        }
