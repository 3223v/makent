# CreateScriptTool Workflow

Create a new script-based local executable tool in `src/script`.

## Workflow Steps

### 1. Inspect Existing Patterns

Read at least one existing tool in `src/script` to match the current conventions. Prefer manifest-based tools when creating something new.

### 2. Define the Tool Contract

Decide:

- tool directory name
- tool name exposed to the model
- JSON schema parameters
- runtime
- entry file
- return shape

Keep the contract minimal and explicit.

### 3. Implement the Tool Directory

Create `src/script/<tool-name>/tool.toml` and the runtime entry file.

The tool package should:

- declare `name`, `description`, `runtime`, `entry`, and `parameters`
- use the runtime's stdin/stdout JSON contract
- raise or emit clear runtime errors on invalid input
- keep execution assets inside the tool directory

### 4. Verify the Shape

Check that the manifest matches the script tool loader expectations used by the runtime.

### 5. Update Docs If Needed

If the tool adds a meaningful new capability, update user-facing docs that list or explain tools.

## Output

Report:

- tool directory created
- exposed tool name
- whether docs were updated

## Guidelines

- Prefer one small tool over one overloaded tool.
- Make parameter descriptions model-friendly.
- Avoid hidden dependencies or hardcoded secrets.
- If the capability is really an external integration boundary, consider whether it belongs in `src/mcp` instead.
