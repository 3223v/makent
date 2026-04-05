# Script Tool Manifest

## Purpose

This document defines the manifest-based script tool format supported by the runtime.

The goal is to let `src/script` host local executable tools across multiple runtimes while preserving a single tool abstraction for the agent.

Legacy Python module tools still work, but new tools should prefer the manifest format.

## Directory Layout

Recommended layout:

```text
src/script/<tool-name>/
  tool.toml
  main.py | index.js | run.ps1 | run.bat | run.sh | main.c | main.cpp | binary.exe
```

Each manifest tool lives in its own directory.

## Manifest File

The manifest file is `tool.toml`.

Required top-level fields:

- `name`
- `description`
- `runtime`
- `entry`
- `parameters`

Optional top-level fields:

- `args_mode`
- `timeout_sec`
- `platforms`
- `compiler`
- `compile_args`

## Minimal Example

```toml
name = "list_directory"
description = "List files and directories inside a target directory."
runtime = "python"
entry = "main.py"
args_mode = "json-stdin"
timeout_sec = 20
platforms = ["windows", "linux", "macos"]

[parameters]
type = "object"
required = ["path"]

[parameters.properties.path]
type = "string"
description = "Directory path to inspect."
```

## Field Semantics

### `name`

The tool name exposed to the model.

Keep it stable. Renaming a tool is a breaking change for prompt-level usage.

### `description`

A concise model-facing description of the capability.

### `runtime`

Supported values:

- `python`
- `node`
- `powershell`
- `bash`
- `cmd`
- `binary`
- `c`
- `cpp`

### `entry`

Path to the entry file relative to the tool directory.

The runtime enforces that the resolved path stays inside the tool directory.

### `parameters`

OpenAI-function-style JSON schema. It should be an object schema.

### `args_mode`

Currently supported value:

- `json-stdin`

The runtime passes the tool call arguments as a JSON object to stdin.

### `timeout_sec`

Per-execution timeout in seconds.

### `platforms`

Optional allowlist:

- `windows`
- `linux`
- `macos`

If present, the tool only runs on matching platforms.

### `compiler`

Optional compiler override for native tools.

Used only with `c` or `cpp`.

### `compile_args`

Optional extra compiler arguments for native tools.

Used only with `c` or `cpp`.

## Execution Protocol

The runtime invokes the selected tool and passes arguments through stdin as JSON.

The tool should:

1. Read stdin
2. Parse the JSON arguments
3. Execute its logic
4. Write the result to stdout

Preferred stdout format:

- JSON object or JSON array

Fallback:

- plain text

If stdout is valid JSON, the runtime parses and returns it as structured data.
If stdout is not valid JSON, the runtime returns it as plain text.

Non-zero exit codes are treated as tool execution failures.

## Runtime Mapping

### Python

```toml
runtime = "python"
entry = "main.py"
```

Execution:

```text
python main.py
```

### Node

```toml
runtime = "node"
entry = "index.js"
```

Execution:

```text
node index.js
```

### PowerShell

```toml
runtime = "powershell"
entry = "run.ps1"
```

Execution:

```text
pwsh -File run.ps1
```

Fallback to `powershell` is used if `pwsh` is unavailable.

### Bash

```toml
runtime = "bash"
entry = "run.sh"
```

Execution:

```text
bash run.sh
```

### CMD

```toml
runtime = "cmd"
entry = "run.bat"
```

Execution:

```text
cmd /c run.bat
```

### Binary

```toml
runtime = "binary"
entry = "tool.exe"
```

Execution:

```text
<entry>
```

### C / C++

```toml
runtime = "cpp"
entry = "main.cpp"
```

The runtime compiles the source into `src/script/<tool-name>/.build/` and reuses the cached binary when it is newer than the source file.

Default compiler resolution:

- `c`: `gcc`, fallback `clang`
- `cpp`: `g++`, fallback `clang++`

If you need something specific, set `compiler` and `compile_args`.

## Authoring Templates

### Python Template

```python
import json
import sys

def main():
    args = json.load(sys.stdin)
    result = {"ok": True, "args": args}
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

### Node Template

```js
const fs = require("fs");

const args = JSON.parse(fs.readFileSync(0, "utf8"));
process.stdout.write(JSON.stringify({ ok: true, args }));
```

### PowerShell Template

```powershell
$inputJson = [Console]::In.ReadToEnd()
$args = $inputJson | ConvertFrom-Json
@{ ok = $true; path = $args.path } | ConvertTo-Json -Compress
```

### Bash Template

```bash
#!/usr/bin/env bash
set -euo pipefail
input="$(cat)"
printf '%s\n' "$input"
```

### CMD Template

Use `cmd` only for simple wrappers. JSON handling is weak compared with PowerShell or Python.

### C++ Template

Use stdin to read JSON text. If you do not want to add a JSON library, keep the tool contract extremely simple or wrap the native binary behind a higher-level runtime.

## Load-Time and Run-Time Failure Modes

Load-time errors:

- malformed `tool.toml`
- missing required fields
- invalid entry path

Run-time errors:

- missing runtime executable in PATH
- non-zero exit code
- timeout
- native compiler missing for `c/cpp`

The runtime now records per-tool load failures instead of crashing the whole process. Use `/status` to inspect load error count.

## Security Rules

- Keep `entry` inside the tool directory.
- Do not hardcode secrets.
- Avoid string-built shell commands when a direct executable path is enough.
- Validate input in the tool itself.
- Keep side effects narrow and explicit.

## Recommendation

For new work:

- prefer `python`, `node`, or `powershell`
- use `bash` and `cmd` only for thin wrappers
- use `binary` for stable prebuilt native tools
- use `c/cpp` only when local compilation is acceptable
