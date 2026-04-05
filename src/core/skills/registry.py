import re
from pathlib import Path

try:
    from .skill import Skill, SkillReference, SkillWorkflow
except ImportError:
    from skill import Skill, SkillReference, SkillWorkflow


LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


class SkillRegistry:
    def __init__(self):
        self.skills = {}

    def register(self, skill: Skill):
        self.skills[skill.name] = skill
        return skill

    def get(self, name: str):
        return self.skills.get(name)

    def entries(self):
        return [skill.to_prompt_entry() for skill in self.skills.values()]

    def load_from_directories(self, paths):
        for path in paths or []:
            self.load_from_directory(path)
        return self

    def load_from_directory(self, path):
        base_path = Path(path)
        if not base_path.exists():
            return self

        for file in base_path.rglob("SKILL.md"):
            self.register(self._parse_skill_file(file))

        return self

    def _parse_skill_file(self, path: Path):
        text = path.read_text(encoding="utf-8")
        frontmatter, body = _split_frontmatter(text)
        sections = _parse_markdown_sections(body)

        when_invoked = sections.get("when invoked", "")
        when_to_use = sections.get("when to use", "") or sections.get("overview", "") or when_invoked
        workflow_text = sections.get("workflow", "") or sections.get("the process", "")
        workflow_routing = sections.get("workflow routing", "")
        reference_text = sections.get("reference", "")
        intro = _collapse_whitespace(_extract_intro(body))

        workflows = _parse_workflow_routes(workflow_routing, base_dir=path.parent)
        references = _parse_references(reference_text, base_dir=path.parent)

        name = frontmatter.get("name") or path.parent.name
        description = frontmatter.get("description") or intro or name

        if not workflow_text and workflows:
            workflow_text = "Use the routing table to select a workflow, then execute the chosen workflow exactly as written."

        constraints = sections.get("core rules", "") or sections.get("security & privacy", "")
        if not constraints and frontmatter.get("allowed-tools"):
            constraints = f"Allowed tools: {frontmatter.get('allowed-tools')}"

        return Skill(
            name=name.strip(),
            description=_collapse_whitespace(description),
            when_to_use=_collapse_whitespace(when_to_use),
            workflow=_collapse_whitespace(workflow_text or intro),
            constraints=_collapse_whitespace(constraints),
            invocation=_collapse_whitespace(when_invoked),
            argument_hint=_collapse_whitespace(frontmatter.get("argument-hint", "")),
            model=_collapse_whitespace(frontmatter.get("model", "")),
            allowed_tools=_collapse_whitespace(frontmatter.get("allowed-tools", "")),
            routing_summary=_collapse_whitespace(workflow_routing),
            workflows=workflows,
            references=references,
            source=str(path.resolve()),
        )


def _split_frontmatter(text: str):
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    if len(lines) < 3:
        return {}, text

    frontmatter_lines = []
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            frontmatter = _parse_frontmatter(frontmatter_lines)
            body = "\n".join(lines[index + 1:])
            return frontmatter, body
        frontmatter_lines.append(lines[index])

    return {}, text


def _parse_frontmatter(lines):
    data = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip().lower()] = value.strip().strip('"').strip("'")
    return data


def _parse_markdown_sections(text: str):
    sections = {}
    current = None
    buffer = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current = line[3:].strip().lower()
            buffer = []
            continue

        if current is not None:
            buffer.append(line)

    if current is not None:
        sections[current] = "\n".join(buffer).strip()

    return sections


def _extract_intro(text: str):
    lines = []
    for line in text.splitlines():
        if line.startswith("## "):
            break
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def _parse_workflow_routes(section_text: str, base_dir: Path):
    routes = []
    if not section_text:
        return routes

    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if "Argument" in stripped and "Workflow" in stripped:
            continue
        if set(stripped.replace("|", "").replace("-", "").replace(" ", "")) == set():
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 3:
            continue

        argument = _collapse_whitespace(cells[0].strip("`"))
        workflow_label, workflow_target = _extract_first_link(cells[1])
        description = _collapse_whitespace(cells[2])

        workflow_path = (base_dir / workflow_target).resolve() if workflow_target else None
        summary = _summarize_markdown_file(workflow_path) if workflow_path and workflow_path.exists() else ""
        routes.append(
            SkillWorkflow(
                argument=argument,
                name=workflow_label or cells[1],
                description=description,
                source=str(workflow_path) if workflow_path and workflow_path.exists() else "",
                summary=summary,
            )
        )

    return routes


def _parse_references(section_text: str, base_dir: Path):
    references = []
    for match in LINK_PATTERN.finditer(section_text or ""):
        name = match.group(1).strip()
        target = match.group(2).strip()
        path = (base_dir / target).resolve()
        summary = _summarize_markdown_file(path) if path.exists() else ""
        references.append(
            SkillReference(
                name=name,
                source=str(path) if path.exists() else "",
                summary=summary,
            )
        )
    return references


def _extract_first_link(text: str):
    match = LINK_PATTERN.search(text or "")
    if not match:
        return "", ""
    return match.group(1).strip(), match.group(2).strip()


def _summarize_markdown_file(path: Path):
    text = path.read_text(encoding="utf-8")
    sections = _parse_markdown_sections(text)
    parts = []

    title = ""
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    if title:
        parts.append(title)

    for key in ("workflow steps", "resolution process", "output", "guidelines", "environment"):
        value = sections.get(key, "")
        if value:
            parts.append(_collapse_whitespace(value))

    if not parts:
        parts.append(_collapse_whitespace(_extract_intro(text)))

    return " ".join(part for part in parts if part).strip()


def _collapse_whitespace(text: str):
    return " ".join((text or "").split())
