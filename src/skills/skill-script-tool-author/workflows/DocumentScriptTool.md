# DocumentScriptTool Workflow

Update documentation for a script-based tool.

## Workflow Steps

### 1. Read the Tool Implementation

Read the tool definition so the documentation matches the real behavior. For manifest-based tools, include both `tool.toml` and the entry file.

### 2. Locate Relevant Docs

Update the files that explain:

- what the tool does
- how it is loaded
- how it should be used

### 3. Keep the Documentation Grounded

Document only behavior that exists in code.

## Output

Report which documentation files were updated and what changed at a high level.

## Guidelines

- Prefer short, factual descriptions.
- Keep examples consistent with the actual schema.
