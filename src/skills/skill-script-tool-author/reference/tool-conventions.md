# Tool Conventions

Reference for authoring script-based tools in this project.

## Environment

Script tools are loaded from `src/script` by the runtime's script tool provider.

The loader supports two shapes:

1. Manifest-based tool directories
2. Legacy Python modules

### Manifest-Based Tool Directory

Recommended layout:

```text
src/script/<tool-name>/
  tool.toml
  main.py | index.js | run.ps1 | run.bat | run.sh | main.cpp | ...
```

Required manifest fields:

- `name`
- `description`
- `runtime`
- `entry`
- `parameters`

Supported runtimes:

- `python`
- `node`
- `powershell`
- `bash`
- `cmd`
- `binary`
- `c`
- `cpp`

Argument passing:

- The runtime sends JSON to stdin.
- The tool should read stdin and emit its result to stdout.
- JSON stdout is preferred.

See also:

- `runtime-templates.md` for runtime selection guidance
- `docs/script-tool-manifest.md` for the full manifest contract

### Legacy Python Module

Legacy modules still work when they expose:

- a `Tool` instance
- or a dict with `name`, `description`, `parameters`, and `func`

## Guidelines

- Prefer manifest-based tools for new work.
- File path: `src/script/<tool-name>/tool.toml`
- Tool name should be stable and descriptive
- `parameters` should be valid object-shaped JSON schema
- `description` should explain the capability in model-friendly language
- Keep entry paths inside the tool directory
- Avoid hardcoded secrets and shell string interpolation
- Avoid side effects outside the declared purpose of the tool
