from pathlib import Path


def read_file(path: str):
    return Path(path).read_text(encoding="utf-8")


read_file_tool = {
    "name": "read_file",
    "description": "Read the full contents of a UTF-8 text file.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to read"}
        },
        "required": ["path"]
    },
    "func": read_file
}
