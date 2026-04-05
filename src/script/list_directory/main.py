import json
import sys
from pathlib import Path


def main():
    args = json.load(sys.stdin)
    target = Path(args["path"]).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(str(target))
    if not target.is_dir():
        raise NotADirectoryError(str(target))

    items = []
    for item in sorted(target.iterdir(), key=lambda value: (value.is_file(), value.name.lower())):
        items.append(
            {
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
            }
        )

    print(json.dumps({"path": str(target), "items": items}, ensure_ascii=False))


if __name__ == "__main__":
    main()
