# Src/core/tools/tool.py

class Tool:
    def __init__(self, name, description, parameters, func):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    def to_openai_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }