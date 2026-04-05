from typing import Any, Dict, List

from .schema import LLMResponse, ToolCall


class LLMClient:
    def __init__(self, api_key: str, model: str, url: str = None, temperature: float = 0, name: str = None):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=url) if url else OpenAI(api_key=api_key)
        self.model = model
        self.url = url
        self.temperature = temperature
        self.name = name or model

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] = None,
        temperature: float = None
    ) -> LLMResponse:
        effective_temperature = self.temperature if temperature is None else temperature
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            temperature=effective_temperature
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
            raw=resp
        )

    def _safe_parse(self, s: str):
        import json

        try:
            return json.loads(s)
        except Exception:
            return {"_raw": s}
