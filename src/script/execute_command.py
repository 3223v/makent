import subprocess
from pathlib import Path
from typing import Optional, Dict


def execute_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 30,
    shell: bool = True
) -> Dict[str, any]:
    """
    在指定工作目录执行系统命令。
    
    Args:
        command: 要执行的系统命令字符串
        cwd: 工作目录路径（可选，默认为当前脚本运行目录）
        timeout: 命令超时时间（秒），默认30秒
        shell: 是否通过shell执行（Windows下建议True，Linux下根据命令复杂度选择）
    
    Returns:
        包含执行结果的字典：returncode（返回码）、stdout（标准输出）、stderr（标准错误）、cwd（工作目录）
    
    Raises:
        FileNotFoundError: 当指定的工作目录不存在时
        subprocess.TimeoutExpired: 当命令执行超时时
    """
    # 验证工作目录
    if cwd is not None:
        work_dir = Path(cwd)
        if not work_dir.exists():
            raise FileNotFoundError(f"Working directory not found: {cwd}")
        if not work_dir.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {cwd}")
        cwd = str(work_dir.absolute())

    # 执行命令
    result = subprocess.run(
        command,
        shell=shell,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace',  # 替换无法解码的字符，避免崩溃
        timeout=timeout
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "cwd": cwd or str(Path.cwd())
    }


execute_command_tool = {
    "name": "execute_command",
    "description": "Execute a system command in a specified working directory. (Warning: Only run trusted commands)",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The system command to execute"},
            "cwd": {"type": "string", "description": "Working directory path (optional)"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)"},
            "shell": {"type": "boolean", "description": "Execute through shell (default: True)"}
        },
        "required": ["command"]
    },
    "func": execute_command
}