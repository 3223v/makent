from dataclasses import dataclass, field


@dataclass
class SkillWorkflow:
    argument: str
    name: str
    description: str = ""
    source: str = ""
    summary: str = ""

    def to_prompt_entry(self):
        return {
            "argument": self.argument,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "summary": self.summary,
        }


@dataclass
class SkillReference:
    name: str
    source: str = ""
    summary: str = ""

    def to_prompt_entry(self):
        return {
            "name": self.name,
            "source": self.source,
            "summary": self.summary,
        }


@dataclass
class Skill:
    name: str
    description: str
    when_to_use: str = ""
    workflow: str = ""
    constraints: str = ""
    invocation: str = ""
    argument_hint: str = ""
    model: str = ""
    allowed_tools: str = ""
    routing_summary: str = ""
    workflows: list[SkillWorkflow] = field(default_factory=list)
    references: list[SkillReference] = field(default_factory=list)
    source: str = ""

    def to_prompt_entry(self):
        return {
            "name": self.name,
            "description": self.description,
            "when_to_use": self.when_to_use,
            "workflow": self.workflow,
            "constraints": self.constraints,
            "invocation": self.invocation,
            "argument_hint": self.argument_hint,
            "model": self.model,
            "allowed_tools": self.allowed_tools,
            "routing_summary": self.routing_summary,
            "workflows": [item.to_prompt_entry() for item in self.workflows],
            "references": [item.to_prompt_entry() for item in self.references],
            "source": self.source,
        }
