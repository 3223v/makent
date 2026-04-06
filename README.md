# Agent Runtime

一个分层实现的 Agent Runtime，当前主链路是 `LLM -> Router -> Agent -> Executor -> Tools`。

这一版的重点是把 `skills` 从 `tools` 中拆出来，并让 runtime 能承接完整的本地 skill 包和 mcp 模块目录：

- `tools` 是可调用的执行能力抽象
- `script` 和未来的 `mcp` 都属于 `tools` 的来源
- `skills` 是规划与使用说明，不直接执行，通过 prompt 注入给模型

详细架构见 [docs/architecture.md](docs/architecture.md)。
Skill 编写规范见 [docs/skill-spec.md](docs/skill-spec.md)。

## 当前状态

- 已实现 `script` tool source
- 已实现 `mcp` tool source，扫描 `src/mcp/*.py`
- 已实现 `skills` 目录加载与 `[Available Skills]` prompt 注入
- 已支持解析 `SKILL.md + workflows/*.md + reference/*.md` 结构
- `skills` 不进入 `ToolRegistry`，不会被当成函数调用

## 目录结构

```text
makent/
├─ README.md
├─ docs/
│  └─ architecture.md
└─ src/
   ├─ config.toml
   ├─ main.py
   ├─ script/
   ├─ prompt/
   └─ core/
      ├─ agent/
      ├─ config/
      ├─ executors/
      ├─ llm/
      ├─ logger/
      ├─ prompt/
      ├─ router/
      ├─ skills/
      └─ tools/
         ├─ providers/
         ├─ tool.py
         └─ tools.py
```

## 架构摘要

### 1. Skills

`skills` 和 `tools` 平级。

`skills` 的职责：

- 告诉模型某种工作流何时使用
- 提供规划步骤、约束和使用建议
- 通过系统 prompt 的 `[Available Skills]` 区块暴露给模型

`skills` 不做的事：

- 不进入 `ToolRegistry`
- 不作为 `tool_call` 执行
- 不要求实现 `func(**kwargs)`

### 2. Tools

`tools` 是统一执行抽象，运行时暴露为 OpenAI function schema。

当前 `tools` 下有两个来源概念：

- `script`
- `mcp`

其中：

- `script` 已实现，扫描 `src/script/*.py`
- `mcp` 已实现为独立 source，扫描 `src/mcp/*.py`

当前 `mcp` 目录里的模块仍然是本地 Python adapter，但它们已经通过 `McpToolProvider` 进入独立 source，而不是再混进 `script` 目录。

### 3. Prompt 注入

系统 prompt 现在会按顺序拼装：

1. core system prompt
2. agent role
3. skill rules
4. tool rules
5. `[Available Skills]`
6. `[Available Tools]`
7. runtime context

这样模型会先知道可用的规划能力，再知道可调用的执行能力。

## 配置

`src/config.toml` 现在支持独立的 `mcp_dir` 和 `skill_dirs`：

```toml
[tools]
script_dir = "script"
mcp_dir = "mcp"
mcp_servers = []

[skills]
skill_dirs = ["skills"]
```

说明：

- `script_dir` 是本地脚本工具目录
- `mcp_dir` 是本地 mcp 模块目录
- `mcp_servers` 仍然保留，后续接远程 MCP server 时使用
- `skill_dirs` 是本地 skills 根目录列表，程序会递归扫描其中的 `SKILL.md`

## Skill 文件格式

最小可用格式示例：

```md
---
name: file-editing
description: Safely edit local text files
---

## When to Use
Use this skill when the task requires reading and editing workspace files.

## Workflow
Inspect first, then make the smallest safe change, then verify.

## Core Rules
Do not invent file contents. Prefer grounded edits and verification.
```

运行时会提取：

- `name`
- `description`
- `When to Use` 或 `When Invoked`
- `Workflow`
- `Workflow Routing`
- `Core Rules`
- `allowed-tools`
- `argument-hint`
- `model`

如果 skill 包里存在：

- `workflows/*.md`
- `reference/*.md`

运行时还会解析这些文档并提取摘要，一起注入到 `[Available Skills]`。

并注入到 `[Available Skills]`。

## 启动

在项目根目录运行：

```powershell
python src/main.py "读取某个文件内容"
```

不带任务参数启动时，会进入交互模式：

```powershell
python src/main.py
```

交互命令：

- `/status`
- `/task "读取某个文件内容"`
- `/help`
- `/exit`

## 后续方向

- 接入远程 MCP server discovery，并把远程 tool 适配到 `McpToolProvider`
- 支持远程 skill 获取与本地缓存
- 为 skill 加入更严格的结构化元数据和版本管理
- 支持模型显式输出“选用了哪个 skill”的规划痕迹
## Script Manifest Tools

The script tool source now supports two formats:

- Legacy Python module tools: `src/script/*.py`
- Manifest-based executable tools: `src/script/<tool-name>/tool.toml`

Manifest tools support these runtimes:

- `python`
- `node`
- `powershell`
- `bash`
- `cmd`
- `binary`
- `c`
- `cpp`

Manifest execution protocol:

- The runtime passes tool arguments as JSON through stdin.
- The tool returns its result through stdout.
- JSON stdout is preferred, but plain text is accepted as a fallback.

Example:

```text
src/script/list_directory/
  tool.toml
  main.py
```
Additional docs:

- [docs/skill-spec.md](docs/skill-spec.md)
- [docs/script-tool-manifest.md](docs/script-tool-manifest.md)

## Per-Client Thinking

Each `[[llm.clients]]` entry can now set:

```toml
thinking_enabled = true
```

or

```toml
thinking_enabled = false
```

This is applied per client, so thinking-enabled and thinking-disabled models can coexist in the same router.

Current provider-aware request mapping:

- `moonshot` -> `thinking = { type = "enabled" | "disabled" }`
- `openrouter` -> `reasoning = { enabled = true | false }`

The runtime also sanitizes message history per client:

- thinking-enabled clients keep reasoning fields
- thinking-disabled clients strip reasoning fields before the request is sent
