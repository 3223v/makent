from pathlib import Path


def create_file(path: str, content: str = "", overwrite: bool = False):
    file_path = Path(path)
    existed = file_path.exists()

    if existed and not overwrite:
        raise FileExistsError(f"{path} already exists")

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

    return {
        "path": str(file_path),
        "created": True,
        "overwritten": existed and overwrite
    }


create_file_tool = {
    "name": "create_file",
    "description": "Create a UTF-8 text file. Can also overwrite when explicitly allowed.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to create"},
            "content": {"type": "string", "description": "Initial file content"},
            "overwrite": {"type": "boolean", "description": "Whether to overwrite an existing file"}
        },
        "required": ["path"]
    },
    "func": create_file
}
