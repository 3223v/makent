---
name: Script Tool Author
description: Create and update script-based tools for this project so the runtime can evolve through local executable capabilities across multiple runtimes.
argument-hint: "<create|update|document> <tool-name>"
allowed-tools: create_file, read_file, update_file
---

Use this skill to evolve the project by adding or refining local script tools under `src/script`.

## When to Use

Use this skill when the user asks to add, update, or document a script-based tool for this runtime.

## When Invoked

1. Inspect the existing tool layout under `src/script`.
2. Determine whether the request is for a new tool, an update to an existing tool, or documentation work.
3. Read the relevant script files before editing them.
4. Follow the routed workflow exactly.
5. If a new tool changes the visible capability set, update the relevant docs.

## Workflow

Use the routing table to select a workflow. Prefer the smallest safe change that produces a valid manifest-based local executable tool. Legacy single-file Python modules still exist, but new tools should prefer the manifest format.

## Workflow Routing

| Argument | Workflow | Description |
|----------|----------|-------------|
| `create <tool-name>` | [CreateScriptTool](./workflows/CreateScriptTool.md) | Create a new script tool in `src/script` |
| `update <tool-name>` | [UpdateScriptTool](./workflows/UpdateScriptTool.md) | Modify an existing script tool implementation |
| `document <tool-name>` | [DocumentScriptTool](./workflows/DocumentScriptTool.md) | Update docs that describe the tool |

## Core Rules

- Script tools belong under `src/script`, not `src/mcp`.
- New tools should prefer `src/script/<tool-name>/tool.toml` plus an entry file.
- Legacy Python module tools are still supported for backward compatibility.
- Prefer ASCII and clear JSON-schema descriptions.
- Keep tool behavior narrowly scoped and deterministic.
- Do not invent a new abstraction if the existing script tool pattern is sufficient.

## Reference

- [Tool Conventions](./reference/tool-conventions.md)
- [Runtime Templates](./reference/runtime-templates.md)
