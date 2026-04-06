import copy
from typing import Any, Dict, List

from .schema import LLMResponse, ToolCall


class LLMClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        provider: str = "custom",
        url: str = None,
        temperature: float = 0,
        name: str = None,
        thinking_enabled: bool | None = None,
    ):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=url) if url else OpenAI(api_key=api_key)
        self.model = model
        self.provider = provider
        self.url = url
        self.temperature = temperature
        self.name = name or model
        self.thinking_enabled = thinking_enabled

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] = None,
        temperature: float = None
    ) -> LLMResponse:
        effective_temperature = self.temperature if temperature is None else temperature
        request_kwargs = {
            "model": self.model,
            "messages": self._prepare_messages(messages),
            "tools": tools,
            "temperature": effective_temperature,
        }
        request_kwargs.update(self._thinking_request_options())

        resp = self.client.chat.completions.create(
            **request_kwargs
        )

        msg = resp.choices[0].message
        tool_calls = []

        if msg.tool_calls:
            for index, call in enumerate(msg.tool_calls, start=1):
                tool_calls.append(
                    ToolCall(
                        id=getattr(call, "id", None) or f"tool_call_{index}",
                        name=call.function.name,
                        arguments=self._safe_parse(call.function.arguments)
                    )
                )

        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            assistant_message=self._message_to_history_dict(msg),
            raw=resp
        )

    def _safe_parse(self, s: str):
        import json

        try:
            return json.loads(s)
        except Exception:
            return {"_raw": s}

    def _message_to_history_dict(self, msg):
        dump = None

        if hasattr(msg, "model_dump"):
            dump = msg.model_dump(exclude_none=True)
        elif hasattr(msg, "to_dict"):
            dump = msg.to_dict()
        elif hasattr(msg, "dict"):
            dump = msg.dict(exclude_none=True)

        if isinstance(dump, dict):
            dump.setdefault("role", "assistant")
            return dump

        message = {"role": "assistant", "content": getattr(msg, "content", None)}

        reasoning_content = getattr(msg, "reasoning_content", None)
        if reasoning_content is not None:
            message["reasoning_content"] = reasoning_content

        raw_tool_calls = getattr(msg, "tool_calls", None)
        if raw_tool_calls:
            message["tool_calls"] = []
            for index, call in enumerate(raw_tool_calls, start=1):
                function = getattr(call, "function", None)
                message["tool_calls"].append(
                    {
                        "id": getattr(call, "id", None) or f"tool_call_{index}",
                        "type": getattr(call, "type", None) or "function",
                        "function": {
                            "name": getattr(function, "name", None),
                            "arguments": getattr(function, "arguments", None),
                        },
                    }
                )

        return message

    def _prepare_messages(self, messages: List[Dict[str, Any]]):
        prepared = copy.deepcopy(messages)
        if self.thinking_enabled is False:
            for message in prepared:
                self._strip_reasoning_fields(message)
        return prepared

    def _thinking_request_options(self):
        if self.thinking_enabled is None:
            return {}

        provider = (self.provider or "").lower()
        enabled = self.thinking_enabled

        if provider == "moonshot":
            return {"extra_body": {"thinking": {"type": "enabled" if enabled else "disabled"}}}

        if provider == "openrouter":
            return {"extra_body": {"reasoning": {"enabled": enabled}}}

        return {}

    def _strip_reasoning_fields(self, value):
        if isinstance(value, dict):
            value.pop("reasoning_content", None)
            value.pop("reasoning", None)
            value.pop("reasoning_details", None)
            for nested in value.values():
                self._strip_reasoning_fields(nested)
            return

        if isinstance(value, list):
            for item in value:
                self._strip_reasoning_fields(item)
