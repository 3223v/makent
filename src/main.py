import argparse
import shlex
from pathlib import Path

try:
    from Src.core.agent import Agent
    from Src.core.config import load_settings
    from Src.core.executors.tool_executor import ToolExecutor
    from Src.core.llm import LLMClient
    from Src.core.logger import ExecutionLogger
    from Src.core.prompt import PromptBuilder
    from Src.core.router import LLMRouter
    from Src.core.skills import SkillRegistry
    from Src.core.tools.providers import McpToolProvider, ScriptToolProvider
    from Src.core.tools.tools import ToolRegistry
except ModuleNotFoundError:
    from core.agent import Agent
    from core.config import load_settings
    from core.executors.tool_executor import ToolExecutor
    from core.llm import LLMClient
    from core.logger import ExecutionLogger
    from core.prompt import PromptBuilder
    from core.router import LLMRouter
    from core.skills import SkillRegistry
    from core.tools.providers import McpToolProvider, ScriptToolProvider
    from core.tools.tools import ToolRegistry


DEFAULT_CONFIG_PATH = Path(__file__).resolve().with_name("config.toml")


def build_agent(config_path=DEFAULT_CONFIG_PATH):
    settings = load_settings(config_path)

    router = LLMRouter(
        clients=[
            LLMClient(
                api_key=client.resolve_api_key(settings.llm.api_key, settings.llm.api_key_env),
                model=client.model,
                url=client.resolve_url(),
                temperature=client.resolve_temperature(settings.llm.temperature),
                name=client.name,
            )
            for client in settings.llm.clients
        ]
    )

    tool_registry = ToolRegistry()
    tool_providers = [
        ScriptToolProvider(settings.tools.script_dir),
        McpToolProvider(settings.tools.mcp_dir, settings.tools.mcp_servers),
    ]
    for provider in tool_providers:
        provider.load_into(tool_registry)

    skill_registry = SkillRegistry().load_from_directories(settings.skills.skill_dirs)

    prompt_builder = PromptBuilder.from_markdown_files(
        settings.prompt.system_prompt_file,
        layer_files=[
            ("Agent Role", settings.prompt.agent_role_file),
            ("Skill Rules", settings.prompt.skill_rules_file),
            ("Tool Rules", settings.prompt.tool_rules_file),
        ]
    )

    return Agent(
        llm=router,
        executor=ToolExecutor(tool_registry),
        prompt_builder=prompt_builder,
        max_steps=settings.agent.max_steps,
        logger_factory=lambda: ExecutionLogger(settings.logging.log_dir),
        skill_registry=skill_registry,
    )


def run_task(task: str, config_path=DEFAULT_CONFIG_PATH, return_state=False):
    agent = build_agent(config_path=config_path)
    return agent.run(
        task,
        context={"workspace": str(Path.cwd())},
        return_state=return_state
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Run the agent runtime in single-task or interactive mode.")
    parser.add_argument("task", nargs="*", help="Task to execute")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the TOML config file"
    )
    return parser.parse_args()


def resolve_task(task_parts):
    if task_parts:
        return " ".join(task_parts).strip()

    task = input("task> ").strip()
    if not task:
        raise ValueError("Task cannot be empty")
    return task


def format_status(agent) -> str:
    skill_names = sorted(skill["name"] for skill in agent.skill_registry.entries()) if agent.skill_registry else []
    tool_names = sorted(schema["function"]["name"] for schema in agent.executor.schemas())
    load_errors = list(getattr(agent.executor.registry, "load_errors", []))

    lines = [
        "[Status]",
        f"workspace={Path.cwd()}",
        f"skills_count={len(skill_names)}",
        f"skills={', '.join(skill_names) if skill_names else '<none>'}",
        f"tools_count={len(tool_names)}",
        f"tools={', '.join(tool_names) if tool_names else '<none>'}",
        f"tool_load_errors={len(load_errors)}",
    ]
    if load_errors:
        lines.append("load_error_details=" + " | ".join(load_errors))
    return "\n".join(lines)


def print_help():
    print("[Commands]")
    print('/status')
    print('/task "your task here"')
    print("/help")
    print("/exit")


def parse_command(line: str):
    if not line.strip():
        return "", ""

    try:
        parts = shlex.split(line)
    except ValueError as exc:
        raise ValueError(f"invalid command syntax: {exc}") from exc

    if not parts:
        return "", ""

    command = parts[0].lower()
    argument = " ".join(parts[1:]).strip()
    return command, argument


def run_interactive(config_path=DEFAULT_CONFIG_PATH, initial_task: str = ""):
    agent = build_agent(config_path=config_path)

    print("Interactive mode. Use /help to list commands.")
    if initial_task:
        print(run_agent_task(agent, initial_task))

    while True:
        raw = input("cmd> ").strip()
        if not raw:
            continue

        try:
            command, argument = parse_command(raw)
        except ValueError as exc:
            print(f"error: {exc}")
            continue

        if command in ("/exit", "/quit"):
            print("bye")
            return

        if command == "/help":
            print_help()
            continue

        if command == "/status":
            print(format_status(agent))
            continue

        if command == "/task":
            if not argument:
                print('error: /task requires an input, for example /task "read a file"')
                continue
            print(run_agent_task(agent, argument))
            continue

        print("error: unknown command. Use /help.")


def run_agent_task(agent, task: str):
    return agent.run(
        task,
        context={"workspace": str(Path.cwd())},
        return_state=False,
    )


if __name__ == "__main__":
    args = parse_args()
    if args.task:
        task = resolve_task(args.task)
        result = run_task(task, config_path=args.config)
        print(result)
    else:
        run_interactive(config_path=args.config)
