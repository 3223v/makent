import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


PROVIDER_PRESETS = {
    "openai": {
        "url": "https://api.openai.com/v1",
        "api_key_env": ["OPENAI_API_KEY"],
        "requires_api_key": True,
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1",
        "api_key_env": ["OPENROUTER_API_KEY"],
        "requires_api_key": True,
    },
    "deepseek": {
        "url": "https://api.deepseek.com/v1",
        "api_key_env": ["DEEPSEEK_API_KEY"],
        "requires_api_key": True,
    },
    "dashscope": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": ["DASHSCOPE_API_KEY"],
        "requires_api_key": True,
    },
    "siliconflow": {
        "url": "https://api.siliconflow.cn/v1",
        "api_key_env": ["SILICONFLOW_API_KEY"],
        "requires_api_key": True,
    },
    "moonshot": {
        "url": "https://api.moonshot.cn/v1",
        "api_key_env": ["MOONSHOT_API_KEY", "KIMI_API_KEY"],
        "requires_api_key": True,
    },
    "ollama": {
        "url": "http://127.0.0.1:11434/v1",
        "api_key_env": [],
        "requires_api_key": False,
    },
    "custom": {
        "url": "",
        "api_key_env": [],
        "requires_api_key": False,
    },
}


@dataclass
class ClientSettings:
    name: str
    model: str
    provider: str = "custom"
    url: str = ""
    api_key: str = ""
    api_key_env: List[str] = field(default_factory=list)
    temperature: Optional[float] = None

    def resolve_url(self) -> str:
        preset = PROVIDER_PRESETS.get(self.provider.lower(), PROVIDER_PRESETS["custom"])
        url = self.url or preset["url"]
        if not url:
            raise RuntimeError(f"LLM client '{self.name}' requires a url")
        return url

    def resolve_api_key(self, default_api_key: str = "", default_api_key_env: Optional[List[str]] = None) -> str:
        preset = PROVIDER_PRESETS.get(self.provider.lower(), PROVIDER_PRESETS["custom"])
        env_candidates = self.api_key_env or preset["api_key_env"] or list(default_api_key_env or [])

        for env_name in env_candidates:
            value = os.getenv(env_name)
            if value:
                return value.strip()

        if self.api_key:
            return self.api_key.strip()

        if default_api_key:
            return default_api_key.strip()

        if preset["requires_api_key"]:
            raise RuntimeError(f"LLM client '{self.name}' has no api key configured")

        return "EMPTY"

    def resolve_temperature(self, default_temperature: float) -> float:
        if self.temperature is None:
            return default_temperature
        return self.temperature


@dataclass
class LLMSettings:
    api_key: str = ""
    api_key_env: List[str] = field(default_factory=lambda: ["OPENROUTER_API_KEY", "OPENAI_API_KEY"])
    temperature: float = 0.0
    clients: List[ClientSettings] = field(default_factory=list)


@dataclass
class AgentSettings:
    max_steps: int = 5


@dataclass
class ToolSettings:
    script_dir: str = "Src/script"
    mcp_dir: str = "Src/mcp"
    mcp_servers: List[str] = field(default_factory=list)


@dataclass
class SkillSettings:
    skill_dirs: List[str] = field(default_factory=lambda: ["Src/skills"])


@dataclass
class PromptSettings:
    system_prompt_file: str = "Src/prompt/sys_prompt/core_sys.md"
    agent_role_file: str = "Src/prompt/layers/agent_role.md"
    skill_rules_file: str = "Src/prompt/layers/skill_rules.md"
    tool_rules_file: str = "Src/prompt/layers/tool_rules.md"


@dataclass
class LoggingSettings:
    log_dir: str = "Src/log"


@dataclass
class AppSettings:
    llm: LLMSettings
    agent: AgentSettings
    tools: ToolSettings
    skills: SkillSettings
    prompt: PromptSettings
    logging: LoggingSettings


def load_settings(config_path="Src/config.toml") -> AppSettings:
    config_file = _resolve_config_path(config_path)
    raw = tomllib.loads(config_file.read_text(encoding="utf-8"))
    config_dir = config_file.parent

    llm_raw = raw.get("llm", {})
    agent_raw = raw.get("agent", {})
    tools_raw = raw.get("tools", {})
    skills_raw = raw.get("skills", {})
    prompt_raw = raw.get("prompt", {})
    logging_raw = raw.get("logging", {})

    clients = _load_llm_clients(llm_raw)
    if not clients:
        raise RuntimeError("At least one LLM client must be configured")

    return AppSettings(
        llm=LLMSettings(
            api_key=llm_raw.get("api_key", ""),
            api_key_env=_normalize_list(llm_raw.get("api_key_env", ["OPENROUTER_API_KEY", "OPENAI_API_KEY"])),
            temperature=float(llm_raw.get("temperature", 0.0)),
            clients=clients,
        ),
        agent=AgentSettings(
            max_steps=int(agent_raw.get("max_steps", 5))
        ),
        tools=ToolSettings(
            script_dir=str(_resolve_runtime_path(tools_raw.get("script_dir", "script"), config_dir)),
            mcp_dir=str(_resolve_runtime_path(tools_raw.get("mcp_dir", "mcp"), config_dir)),
            mcp_servers=_normalize_list(tools_raw.get("mcp_servers", []))
        ),
        skills=SkillSettings(
            skill_dirs=[
                str(_resolve_runtime_path(path_value, config_dir))
                for path_value in _normalize_list(skills_raw.get("skill_dirs", ["skills"]))
            ]
        ),
        prompt=PromptSettings(
            system_prompt_file=str(
                _resolve_runtime_path(prompt_raw.get("system_prompt_file", "prompt/sys_prompt/core_sys.md"), config_dir)
            ),
            agent_role_file=str(
                _resolve_runtime_path(prompt_raw.get("agent_role_file", "prompt/layers/agent_role.md"), config_dir)
            ),
            skill_rules_file=str(
                _resolve_runtime_path(prompt_raw.get("skill_rules_file", "prompt/layers/skill_rules.md"), config_dir)
            ),
            tool_rules_file=str(
                _resolve_runtime_path(prompt_raw.get("tool_rules_file", "prompt/layers/tool_rules.md"), config_dir)
            )
        ),
        logging=LoggingSettings(
            log_dir=str(_resolve_runtime_path(logging_raw.get("log_dir", "log"), config_dir))
        )
    )


def _load_llm_clients(llm_raw) -> List[ClientSettings]:
    clients_raw = llm_raw.get("clients", [])
    if clients_raw:
        return [
            ClientSettings(
                name=client.get("name", f"client-{index}"),
                model=client["model"],
                provider=client.get("provider", "custom"),
                url=client.get("url", ""),
                api_key=client.get("api_key", ""),
                api_key_env=_normalize_list(client.get("api_key_env", [])),
                temperature=_optional_float(client.get("temperature")),
            )
            for index, client in enumerate(clients_raw, start=1)
        ]

    legacy_models_raw = llm_raw.get("models", [])
    return [
        ClientSettings(
            name=model.get("alias", model["name"]),
            model=model["name"],
            provider=model.get("provider", "custom"),
            url=model.get("url", ""),
            api_key=model.get("api_key", ""),
            api_key_env=_normalize_list(model.get("api_key_env", [])),
            temperature=_optional_float(model.get("temperature")),
        )
        for model in legacy_models_raw
    ]


def _normalize_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _optional_float(value):
    if value is None:
        return None
    return float(value)


def _resolve_config_path(config_path: str) -> Path:
    raw_path = Path(config_path)
    if raw_path.is_absolute() and raw_path.exists():
        return raw_path

    candidates = [
        Path.cwd() / raw_path,
        Path(__file__).resolve().parents[2] / raw_path.name,
        Path(__file__).resolve().parents[3] / raw_path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise FileNotFoundError(f"Config file not found: {config_path}")


def _resolve_runtime_path(path_value: str, config_dir: Path) -> Path:
    raw_path = Path(path_value)
    if raw_path.is_absolute():
        return raw_path

    candidates = [
        config_dir / raw_path,
        config_dir.parent / raw_path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return (config_dir / raw_path).resolve()
