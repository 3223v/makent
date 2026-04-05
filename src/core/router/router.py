# Src/core/router/router.py

from typing import List
from ..llm import LLMClient


class LLMRouter:
    def __init__(self, clients: List[LLMClient]):
        self.clients = clients
        self.index = 0

    def chat(self, *args, **kwargs):
        last_error = None

        # 轮询 + fallback
        for i in range(len(self.clients)):
            client = self.clients[(self.index + i) % len(self.clients)]

            try:
                resp = client.chat(*args, **kwargs)
                # 成功后推进 index（负载均衡）
                self.index = (self.index + i + 1) % len(self.clients)
                return resp
            except Exception as e:
                last_error = e
                continue

        raise Exception(f"All LLM clients failed: {last_error}")