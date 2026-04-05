# UpdateScriptTool Workflow

Update an existing script-based tool in `src/script`.

## Workflow Steps

### 1. Read the Existing Tool

Read the current tool definition completely before changing it. For manifest-based tools, read both `tool.toml` and the entry file.

### 2. Identify the Change Scope

Determine whether the change affects:

- implementation only
- parameter schema
- exposed tool name
- runtime or entry file
- documentation

### 3. Apply the Smallest Safe Edit

Prefer updating only the necessary function body, schema entries, or descriptions.

### 4. Preserve Loader Compatibility

Do not break the expected loader shape. Manifest-based tools must keep a valid `tool.toml`. Legacy Python module tools must still expose a valid tool object or tool dict.

### 5. Update Docs If the Contract Changed

If tool behavior or parameters changed in a user-visible way, update the relevant documentation.

## Output

Report:

- tool files updated
- contract changed or unchanged
- docs changed or unchanged

## Guidelines

- Preserve backward compatibility unless the user explicitly asked for a breaking change.
- Keep schema descriptions synchronized with implementation behavior.
- Do not silently rename the exposed tool.
