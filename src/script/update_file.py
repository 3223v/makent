from pathlib import Path


def update_file(path: str, old_text: str, new_text: str, replace_all: bool = False):
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(path)
    if old_text == "":
        raise ValueError("old_text cannot be empty")

    content = file_path.read_text(encoding="utf-8")
    occurrences = content.count(old_text)

    if occurrences == 0:
        raise ValueError("old_text not found in file")

    if replace_all:
        updated = content.replace(old_text, new_text)
        replaced_count = occurrences
    else:
        updated = content.replace(old_text, new_text, 1)
        replaced_count = 1

    file_path.write_text(updated, encoding="utf-8")

    return {
        "path": str(file_path),
        "replaced_count": replaced_count
    }


update_file_tool = {
    "name": "update_file",
    "description": "Modify a UTF-8 text file by replacing existing text with new text.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to update"},
            "old_text": {"type": "string", "description": "Existing text to replace"},
            "new_text": {"type": "string", "description": "Replacement text"},
            "replace_all": {"type": "boolean", "description": "Whether to replace every occurrence"}
        },
        "required": ["path", "old_text", "new_text"]
    },
    "func": update_file
}
