import importlib
import tomllib
from pathlib import Path

try:
    from .local_executable import ExecutableToolSpec, LocalExecutableRunner
    from .tool import Tool
except ImportError:
    from local_executable import ExecutableToolSpec, LocalExecutableRunner
    from tool import Tool


class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.load_errors = []
        self.local_runner = LocalExecutableRunner()

    def register(self, tool):
        self.tools[tool.name] = tool
        return tool

    def get(self, name):
        return self.tools.get(name)

    def schemas(self):
        return [tool.to_openai_schema() for tool in self.tools.values()]

    def load_from_scripts(self, path=None):
        base_path = Path(path) if path else Path(__file__).resolve().parents[2] / "script"
        self.load_from_script_manifests(base_path)
        self.load_from_module_directory(
            path=base_path,
            package_candidates=["Src.script", "script"],
        )
        return self

    def load_from_mcp_modules(self, path=None):
        self.load_from_module_directory(
            path=path if path else Path(__file__).resolve().parents[2] / "mcp",
            package_candidates=["Src.mcp", "mcp"],
        )
        return self

    def load_from_module_directory(self, path, package_candidates):
        base_path = Path(path)
        if not base_path.exists():
            return self

        for file in base_path.glob("*.py"):
            if file.name.startswith("_"):
                continue

            try:
                module = self._import_module(file.stem, package_candidates)
                self._register_module_objects(module)
            except Exception as exc:
                self.load_errors.append(f"{file}: {exc}")

        return self

    def load_from_script_manifests(self, path):
        base_path = Path(path)
        if not base_path.exists():
            return self

        for manifest_file in base_path.glob("*/tool.toml"):
            try:
                self.register(self._tool_from_manifest(manifest_file))
            except Exception as exc:
                self.load_errors.append(f"{manifest_file}: {exc}")

        return self

    def _import_module(self, stem, package_candidates):
        last_exc = None
        for package_name in package_candidates:
            try:
                return importlib.import_module(f"{package_name}.{stem}")
            except ModuleNotFoundError as exc:
                last_exc = exc

        if last_exc:
            raise last_exc
        raise ModuleNotFoundError(stem)

    def _register_module_objects(self, module):
        for attr in dir(module):
            obj = getattr(module, attr)

            if isinstance(obj, Tool):
                self.register(obj)
                continue

            if isinstance(obj, dict) and {"name", "description", "parameters", "func"} <= obj.keys():
                self.register(
                    Tool(
                        name=obj["name"],
                        description=obj["description"],
                        parameters=obj["parameters"],
                        func=obj["func"]
                    )
                )

    def _tool_from_manifest(self, manifest_path: Path):
        raw = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        spec = ExecutableToolSpec(
            name=str(raw["name"]),
            description=str(raw["description"]),
            parameters=raw["parameters"],
            runtime=str(raw["runtime"]),
            entry=str(raw["entry"]),
            tool_dir=manifest_path.parent.resolve(),
            args_mode=str(raw.get("args_mode", "json-stdin")),
            timeout_sec=int(raw.get("timeout_sec", 30)),
            platforms=[str(item) for item in raw.get("platforms", [])],
            compiler=str(raw.get("compiler", "")),
            compile_args=[str(item) for item in raw.get("compile_args", [])],
        )

        def manifest_func(**kwargs):
            return self.local_runner.run(spec, kwargs)

        return Tool(
            name=spec.name,
            description=spec.description,
            parameters=spec.parameters,
            func=manifest_func,
        )
