# Skill Specification

## Purpose

This document defines the skill package format supported by the current runtime.

Skills are planning resources, not executable tools. The runtime loads skill packages from configured `skill_dirs`, parses their metadata and supporting documents, then injects a structured `[Available Skills]` section into the system prompt.

The parser is rule-based string parsing. It does not call an LLM to interpret skills.

## Package Layout

A skill package is a directory that contains a `SKILL.md` file.

Recommended layout:

```text
skills/
└─ skill-name/
   ├─ SKILL.md
   ├─ workflows/
   │  ├─ WorkflowA.md
   │  └─ WorkflowB.md
   └─ reference/
      └─ ReferenceA.md
```

Only `SKILL.md` is required. `workflows/` and `reference/` are optional but strongly recommended.

## SKILL.md Frontmatter

The runtime reads YAML-like frontmatter between the first pair of `---` lines.

Supported keys:

- `name`
- `description`
- `argument-hint`
- `model`
- `allowed-tools`

Example:

```md
---
name: Git
description: Git operations for commit, push, rebase, amend, reword, and squash.
argument-hint: "<command> [args]"
model: sonnet
allowed-tools: Bash(git:*), Read, Edit
---
```

Notes:

- Parsing is line-based `key: value`.
- Multiline YAML values are not supported.
- Unknown keys are ignored by the current runtime.

## Supported Sections

The runtime parses `##` headings in `SKILL.md`.

Recognized sections:

- `## When to Use`
- `## When Invoked`
- `## Workflow`
- `## Workflow Routing`
- `## Core Rules`
- `## Security & Privacy`
- `## Reference`
- `## Overview`
- `## The Process`

Field mapping:

- `When to Use` or `Overview` -> `when_to_use`
- `When Invoked` -> `invocation`
- `Workflow` or `The Process` -> `workflow`
- `Core Rules` or `Security & Privacy` -> `constraints`
- `Workflow Routing` -> parsed routes
- `Reference` -> parsed references

If `Workflow` is missing but `Workflow Routing` exists, the runtime inserts a default workflow summary saying the model should select a route and execute the chosen workflow as written.

## Workflow Routing Format

`## Workflow Routing` should use a Markdown table.

Expected shape:

```md
## Workflow Routing

| Argument | Workflow | Description |
|----------|----------|-------------|
| `create <name>` | [CreateTool](./workflows/CreateTool.md) | Create a new tool |
| `update <name>` | [UpdateTool](./workflows/UpdateTool.md) | Update an existing tool |
```

Rules:

- The runtime reads table rows line-by-line.
- The `Workflow` column should contain a Markdown link to a local `.md` file.
- The linked file is loaded and summarized into the prompt.
- The `Argument` text is injected as route selector text.

## Reference Format

`## Reference` should contain Markdown links to local `.md` files.

Example:

```md
## Reference

- [Tool Conventions](./reference/tool-conventions.md)
- [Safety Rules](./reference/safety.md)
```

Rules:

- The runtime scans the section for Markdown links.
- Each linked file is loaded and summarized into the prompt.

## Workflow and Reference Documents

Workflow and reference docs are plain Markdown files. The runtime summarizes them using rule-based extraction.

It looks for these sections first:

- `## Workflow Steps`
- `## Resolution Process`
- `## Output`
- `## Guidelines`
- `## Environment`

If none of those sections exist, it falls back to the title and intro text.

This means you should prefer explicit headings and concise prose.

## Prompt Injection

Each loaded skill is injected with these fields when available:

- `name`
- `description`
- `when_to_use`
- `invocation`
- `argument_hint`
- `model`
- `workflow`
- `allowed_tools`
- `constraints`
- `routes`
- `references`

Workflow and reference docs are injected as summaries, not verbatim full text.

## Parser Limitations

Current limitations:

- No true YAML parser
- No multiline frontmatter values
- Only `##` headings are recognized as sections
- Workflow routing depends on Markdown table structure
- Reference parsing depends on Markdown links
- Summaries are string-based extraction, not semantic LLM summarization

Write skills in a disciplined format if you want predictable runtime behavior.

## Recommended Authoring Rules

- Keep frontmatter single-line per field.
- Always include `name` and `description`.
- Add `## When to Use` or `## When Invoked`.
- Use `## Workflow Routing` when the skill supports multiple subcommands.
- Put operational detail in `workflows/*.md`.
- Put reusable background knowledge in `reference/*.md`.
- Prefer short, imperative workflow steps.
- Make local links explicit and relative to `SKILL.md`.

## Minimal Example

```md
---
name: Script Tool Author
description: Create and update script-based tools for this project.
argument-hint: "<create|update> <tool-name>"
allowed-tools: create_file, read_file, update_file
---

Use this skill to evolve the project by adding or refining local script tools.

## When to Use

Use this skill when the task is to add or update a tool under `src/script`.

## Workflow Routing

| Argument | Workflow | Description |
|----------|----------|-------------|
| `create <tool-name>` | [CreateScriptTool](./workflows/CreateScriptTool.md) | Create a new script tool |
| `update <tool-name>` | [UpdateScriptTool](./workflows/UpdateScriptTool.md) | Update an existing script tool |

## Reference

- [Tool Conventions](./reference/tool-conventions.md)
```

## Runtime Checklist

Before relying on a new skill package:

1. Put it under one of the configured `skill_dirs`.
2. Ensure it contains `SKILL.md`.
3. Ensure any linked workflow/reference docs exist.
4. Start the runtime and run `/status`.
5. Confirm the new skill appears in the loaded skill list.

For manifest-based local executable tools, see [script-tool-manifest.md](./script-tool-manifest.md).
