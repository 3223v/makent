# Architecture

## 目标

这个项目把 Agent Runtime 拆成两条并列的能力线：

- `skills`: 规划层
- `tools`: 执行层

这样可以避免把所有外部能力都粗暴塞进 `tool_call`。

## 核心分层

```text
Agent
├─ Prompt Context
│  ├─ system prompt
│  ├─ available skills
│  ├─ available tools
│  └─ runtime context
├─ Skill Layer
│  └─ SkillRegistry
└─ Tool Layer
   ├─ ToolRegistry
   └─ ToolProviders
      ├─ ScriptToolProvider
      └─ McpToolProvider
```

## Skills

### 定义

`skills` 是规划资源，不是运行时函数。

它描述的是：

- 什么时候用
- 如何规划
- 执行时遵守什么约束

### 为什么不放进 tools

因为 `skills` 不满足 `Tool(name, description, parameters, func)` 这个执行模型。

如果把 skill 强行变成 tool，会出现几个问题：

- skill 没有自然的参数 schema
- skill 的本质是流程指导，不是一次函数调用
- tool executor 无法表达“先选 skill，再用多个 tools 完成步骤”

所以 `skills` 应该单独建模，然后通过 prompt 提供给模型。

### 当前实现

`SkillRegistry` 会扫描配置中的 `skill_dirs`，递归加载 `SKILL.md`。

当前会提取这些字段：

- frontmatter: `name`, `description`
- frontmatter: `argument-hint`, `model`, `allowed-tools`
- markdown sections: `When to Use`, `When Invoked`, `Workflow`, `Workflow Routing`, `Core Rules`

如果 skill 包内部存在配套文档：

- `workflows/*.md`
- `reference/*.md`

运行时还会解析路由表中的本地链接，并把 workflow/reference 文档摘要一并注入。

加载后，`PromptBuilder` 会生成 `[Available Skills]` 区块。

## Tools

### 定义

`tools` 是统一执行抽象，最终都要变成可调用对象：

```python
Tool(name, description, parameters, func)
```

### Tool Sources

`tools` 的下一层是 provider。

当前定义了：

- `ScriptToolProvider`
- `McpToolProvider`

这两个 provider 的地位是平级的。

### Script

`script` 是已经实现的 provider。

它负责扫描本地 `script_dir` 下的 `.py` 文件，并把里面暴露的：

- `Tool` 实例
- 或 `{name, description, parameters, func}` 字典

统一注册到 `ToolRegistry`。

### MCP

`mcp` 也是 tool source。

当前实现是：

- 扫描 `src/mcp/*.py`
- 把模块中暴露的 `Tool` 实例或 `{name, description, parameters, func}` 字典注册为 tool

这里把它保留为独立 `McpToolProvider` 的原因是：

- 明确 MCP 属于 tools 层
- 避免把 MCP source 混进 script source
- 给未来的 session、auth、discovery、schema 适配保留正式入口

这意味着当前目录式 MCP 只是过渡形态，但已经进入独立 source，而不是脚本目录。

## Prompt 组装

当前系统 prompt 的拼装顺序是：

1. core system prompt
2. agent role
3. tool rules
4. available skills
5. available tools
6. runtime context

这个顺序的意图是：

- 先给模型全局规则
- 再给模型规划资源
- 最后给模型执行能力

## Main Wiring

`main.py` 现在做三件事：

1. 创建 `ToolRegistry`，并依次调用各个 `ToolProvider`
2. 创建 `SkillRegistry`，加载本地 skills
3. 把 `ToolExecutor` 和 `SkillRegistry` 一起交给 `Agent`

`Agent` 不执行 skill，只在构造系统 prompt 时把 skill 信息注入进去。

## 当前边界

已经实现：

- `SkillRegistry`
- `PromptBuilder` 的 skill 注入
- `ToolProvider` 抽象
- `ScriptToolProvider`
- `McpToolProvider` 的本地目录扫描
- workflow/reference skill 文档摘要注入

还没有实现：

- 远程 MCP server discovery
- 远程 MCP schema 到 `Tool` 的适配
- 远程 skill 获取
- skill 的版本、缓存、签名校验

## 后续建议

### MCP

后续接远程 MCP 时，建议遵守这个方向：

- `McpToolProvider` 负责 server 连接、tool discovery、schema 转换
- 发现到的 MCP tool 直接注册成 `Tool`
- 不要把远程 MCP 强制先落成 script 文件再加载

### Skills

后续 skill 如果需要远程安装或同步，建议分两层：

- `SkillSource`: 负责发现、拉取、缓存 skill 文件
- `SkillRegistry`: 负责解析、注册、供 prompt 注入

这样能保持“获取”和“使用”分离。
