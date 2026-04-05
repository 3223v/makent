import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class PromptLayer:
    title: str
    content: str


class PromptBuilder:
    def __init__(self, core_prompt: str = "", layers: Optional[List[PromptLayer]] = None):
        self.core_prompt = core_prompt.strip()
        self.layers = layers or []

    @classmethod
    def from_file(cls, path: str):
        return cls(core_prompt=Path(path).read_text(encoding="utf-8"))

    @classmethod
    def from_markdown_files(cls, core_prompt_path: str, layer_files: Optional[List[tuple[str, str]]] = None):
        builder = cls.from_file(core_prompt_path)

        for title, path in layer_files or []:
            builder.add_layer(title, Path(path).read_text(encoding="utf-8"))

        return builder

    def add_layer(self, title: str, content: str):
        self.layers.append(PromptLayer(title=title, content=content.strip()))
        return self

    def build(
        self,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[Iterable[Dict[str, Any]]] = None,
        skills: Optional[Iterable[Dict[str, Any]]] = None,
    ):
        sections = []

        if self.core_prompt:
            sections.append(self.core_prompt)

        for layer in self.layers:
            if layer.content:
                sections.append(f"[{layer.title}]\n{layer.content}")

        skill_section = self._build_skill_section(skills or [])
        if skill_section:
            sections.append(skill_section)

        tool_section = self._build_tool_section(tools or [])
        if tool_section:
            sections.append(tool_section)

        context_section = self._build_context_section(context or {})
        if context_section:
            sections.append(context_section)

        return "\n\n".join(section for section in sections if section.strip())

    def _build_tool_section(self, tools: Iterable[Dict[str, Any]]):
        lines = []

        for tool in tools:
            function = tool.get("function", {})
            name = function.get("name", "unknown")
            description = function.get("description", "")
            parameters = function.get("parameters", {})
            lines.append(
                f"- {name}: {description}\n  parameters={json.dumps(parameters, ensure_ascii=False, default=str)}"
            )

        if not lines:
            return ""

        return "[Available Tools]\n" + "\n".join(lines)

    def _build_skill_section(self, skills: Iterable[Dict[str, Any]]):
        lines = []

        for skill in skills:
            name = skill.get("name", "unknown")
            description = skill.get("description", "")
            when_to_use = skill.get("when_to_use", "")
            workflow = skill.get("workflow", "")
            constraints = skill.get("constraints", "")
            invocation = skill.get("invocation", "")
            argument_hint = skill.get("argument_hint", "")
            model = skill.get("model", "")
            allowed_tools = skill.get("allowed_tools", "")
            workflows = skill.get("workflows", [])
            references = skill.get("references", [])

            parts = [f"- {name}: {description}"]
            if when_to_use:
                parts.append(f"  when_to_use={when_to_use}")
            if invocation:
                parts.append(f"  invocation={invocation}")
            if argument_hint:
                parts.append(f"  argument_hint={argument_hint}")
            if model:
                parts.append(f"  model={model}")
            if workflow:
                parts.append(f"  workflow={workflow}")
            if allowed_tools:
                parts.append(f"  allowed_tools={allowed_tools}")
            if workflows:
                parts.append("  routes:")
                for item in workflows:
                    route_parts = [
                        f"    - {item.get('argument', '')}: {item.get('name', '')}",
                    ]
                    if item.get("description"):
                        route_parts.append(f"      description={item.get('description')}")
                    if item.get("summary"):
                        route_parts.append(f"      summary={item.get('summary')}")
                    parts.extend(route_parts)
            if references:
                parts.append("  references:")
                for item in references:
                    ref_line = f"    - {item.get('name', '')}"
                    if item.get("summary"):
                        ref_line += f": {item.get('summary')}"
                    parts.append(ref_line)
            if constraints:
                parts.append(f"  constraints={constraints}")
            lines.append("\n".join(parts))

        if not lines:
            return ""

        return "[Available Skills]\n" + "\n".join(lines)

    def _build_context_section(self, context: Dict[str, Any]):
        if not context:
            return ""

        return "[Runtime Context]\n" + json.dumps(context, ensure_ascii=False, indent=2, default=str)
