# Runtime Templates

Reference for choosing a runtime when authoring a manifest-based script tool.

## Guidelines

- Choose `python` for the fastest implementation inside this repo.
- Choose `node` when the capability is naturally JavaScript-based.
- Choose `powershell` for Windows shell automation with better JSON support than `cmd`.
- Choose `bash` or `cmd` only for thin wrappers.
- Choose `binary` for stable precompiled native tooling.
- Choose `c/cpp` only if compile-time overhead is acceptable and the machine has a working compiler.

## Output

All runtimes should follow the same contract:

- read JSON arguments from stdin
- emit the result to stdout
- prefer JSON stdout

## Environment

The runtime supports:

- `python`
- `node`
- `powershell`
- `bash`
- `cmd`
- `binary`
- `c`
- `cpp`
