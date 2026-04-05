from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class ExecutionLogger:
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_id = self._next_log_id()
        self.log_path = self.log_dir / f"{self.log_id}.txt"
        self._write_header()

    def log_run_start(self, task: str, context: Optional[Dict[str, Any]] = None):
        self._append_line("[Run Start]")
        self._append_line(f"task: {task}")
        if context:
            self._append_line("context:")
            for key, value in context.items():
                self._append_line(f"  {key}: {value}")
        self._append_line("")

    def log_system_prompt(self, content: str):
        self._append_block("[System Prompt]", content)

    def log_llm_response(self, step: int, content: Optional[str], tool_calls: Iterable[Any]):
        self._append_line(f"[Step {step}]")
        self._append_line("assistant_content:")
        self._append_multiline(content or "<empty>")

        calls = list(tool_calls or [])
        if not calls:
            self._append_line("tool_calls: []")
            self._append_line("")
            return

        self._append_line("tool_calls:")
        for call in calls:
            self._append_line(
                f"  - id={call.id}, name={call.name}, arguments={call.arguments}"
            )
        self._append_line("")

    def log_tool_result(
        self,
        step: int,
        tool_name: str,
        tool_call_id: Optional[str],
        success: bool,
        content: str
    ):
        self._append_line(f"[Step {step} Tool Result]")
        self._append_line(f"tool_name: {tool_name}")
        self._append_line(f"tool_call_id: {tool_call_id}")
        self._append_line(f"success: {success}")
        self._append_line("content:")
        self._append_multiline(content)
        self._append_line("")

    def log_finish(self, reason: str, output: str):
        self._append_line("[Run Finish]")
        self._append_line(f"reason: {reason}")
        self._append_line("final_output:")
        self._append_multiline(output)
        self._append_line("")

    def _next_log_id(self) -> int:
        ids = []
        for path in self.log_dir.glob("*.txt"):
            try:
                ids.append(int(path.stem))
            except ValueError:
                continue
        return (max(ids) + 1) if ids else 1

    def _write_header(self):
        header = [
            f"log_id: {self.log_id}",
            f"created_at: {datetime.now().isoformat(timespec='seconds')}",
            ""
        ]
        self.log_path.write_text("\n".join(header), encoding="utf-8")

    def _append_block(self, title: str, content: str):
        self._append_line(title)
        self._append_multiline(content)
        self._append_line("")

    def _append_multiline(self, content: str):
        lines = str(content).splitlines() or [""]
        for line in lines:
            self._append_line(f"  {line}")

    def _append_line(self, line: str):
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{line}\n")
