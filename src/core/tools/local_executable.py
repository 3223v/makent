import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExecutableToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    runtime: str
    entry: str
    tool_dir: Path
    args_mode: str = "json-stdin"
    timeout_sec: int = 30
    platforms: list[str] = field(default_factory=list)
    compiler: str = ""
    compile_args: list[str] = field(default_factory=list)


class LocalExecutableRunner:
    def run(self, spec: ExecutableToolSpec, arguments: dict[str, Any]):
        self._ensure_platform_allowed(spec)
        payload = self._encode_arguments(spec, arguments)
        command = self._build_command(spec)

        result = subprocess.run(
            command,
            input=payload,
            text=True,
            capture_output=True,
            timeout=spec.timeout_sec,
            cwd=str(spec.tool_dir),
            shell=False,
        )

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        if result.returncode != 0:
            raise RuntimeError(stderr or stdout or f"process exited with code {result.returncode}")

        if not stdout:
            return {"ok": True, "stdout": "", "stderr": stderr}

        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return stdout

    def _encode_arguments(self, spec: ExecutableToolSpec, arguments: dict[str, Any]):
        if spec.args_mode != "json-stdin":
            raise ValueError(f"unsupported args_mode: {spec.args_mode}")
        return json.dumps(arguments, ensure_ascii=False)

    def _build_command(self, spec: ExecutableToolSpec):
        entry = self._resolve_entry(spec)
        runtime = spec.runtime.lower()

        if runtime == "python":
            return [sys.executable, str(entry)]
        if runtime == "node":
            return [self._require_executable(["node"]), str(entry)]
        if runtime == "powershell":
            return [self._require_executable(["pwsh", "powershell"]), "-File", str(entry)]
        if runtime == "bash":
            return [self._require_executable(["bash"]), str(entry)]
        if runtime == "cmd":
            return [self._require_executable(["cmd.exe", "cmd"]), "/c", str(entry)]
        if runtime == "binary":
            return [str(entry)]
        if runtime in {"c", "cpp", "c++"}:
            return [str(self._build_native_binary(spec, entry))]

        raise ValueError(f"unsupported runtime: {spec.runtime}")

    def _build_native_binary(self, spec: ExecutableToolSpec, source_path: Path):
        build_dir = spec.tool_dir / ".build"
        build_dir.mkdir(parents=True, exist_ok=True)

        suffix = ".exe" if sys.platform.startswith("win") else ""
        binary_path = build_dir / f"{source_path.stem}{suffix}"

        if binary_path.exists() and binary_path.stat().st_mtime >= source_path.stat().st_mtime:
            return binary_path

        compiler = spec.compiler or self._default_compiler(spec.runtime.lower())
        command = [compiler, str(source_path), "-o", str(binary_path), *[str(item) for item in spec.compile_args]]

        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=max(spec.timeout_sec, 60),
            cwd=str(spec.tool_dir),
            shell=False,
        )

        if result.returncode != 0:
            raise RuntimeError(f"build failed: {(result.stderr or result.stdout or '').strip()}")

        return binary_path

    def _default_compiler(self, runtime: str):
        if runtime == "c":
            return self._require_executable(["gcc", "clang"])
        return self._require_executable(["g++", "clang++"])

    def _resolve_entry(self, spec: ExecutableToolSpec):
        tool_root = spec.tool_dir.resolve()
        entry_path = (tool_root / spec.entry).resolve()
        if tool_root not in entry_path.parents and entry_path != tool_root:
            raise ValueError("entry must stay inside the tool directory")
        if not entry_path.exists():
            raise FileNotFoundError(str(entry_path))
        return entry_path

    def _ensure_platform_allowed(self, spec: ExecutableToolSpec):
        if not spec.platforms:
            return

        current = self._current_platform_name()
        if current not in {item.lower() for item in spec.platforms}:
            raise RuntimeError(f"tool {spec.name} is not enabled for platform {current}")

    def _current_platform_name(self):
        if sys.platform.startswith("win"):
            return "windows"
        if sys.platform == "darwin":
            return "macos"
        return "linux"

    def _require_executable(self, names: list[str]):
        for name in names:
            resolved = shutil.which(name)
            if resolved:
                return resolved
        raise RuntimeError(f"required executable not found: {', '.join(names)}")
