# Relay Skill

[EN](README.md) | 中文

Relay 是一个面向 coding agent 的轻量级 pass/pickup 接力 skill。

它帮助你干净地结束一个已经很拥挤的 session，开启一个新的 session，并且不用手动重写所有上下文就能继续同一项工作。

## 快速开始

不想思考当前应该 pass 还是 pickup 时，直接使用智能命令：

```text
/relay
```

想显式指定模式时，使用：

```text
/relay-pass
/relay-pickup
```

整体流程很简单：

```text
很满的 session
  -> /relay 或 /relay-pass
  -> Relay 写出一份 handoff 文档
  -> 新 session
  -> /relay 或 /relay-pickup
  -> agent 读取 handoff 并继续工作
```

内置默认行为：

- 新的 Relay 文件会写入当前项目的 `.relay/`。
- Relay 默认写精简版 handoff 文档。
- `.relay/` 会被本仓库的 `.gitignore` 规则忽略；除非你明确要版本化，否则应把它当作本地工作状态。

## 为什么需要它

现在的 coding-agent 工作流早已不只是一个聊天框。很多开发者会在 `.claude/`、`.opencode/` 或全局 skill 目录里维护自己的个性化 harness。项目里也常常会有 `CLAUDE.md`、`AGENTS.md`、rules、playbooks 等文件；这些内容会在每个 session 开始时自动注入，让 agent 一开始就拿到正确的运行上下文。

这在 session 刚开始时很好用。问题通常出现在后半段：当一个 session 已经经历了很多轮对话、很长的工具输出、失败的探索、局部计划和微妙决策之后，你仍然想基于当前状态继续工作。最自然的做法是 compact 当前 session 然后继续。但这取决于具体 runtime 的设计：自动注入的信息可能被压缩或模糊化，session 管理也不够优雅、不易追溯，一些重要细节可能丢失，最终影响输出质量。

另一个办法是新开 session，然后手动写一段精心整理的 prompt 描述当前情况。这通常是更好的工程卫生，但非常消耗心神。你需要记住改过什么、哪里失败了、哪些约束重要、下一个 agent 应该先做什么。

Relay 就是为这个空隙而生的：把接力棒从一个 session 传给下一个 session。

Matt Pocock 出色的 [`handoff`](https://skills.sh/mattpocock/skills/handoff) skill 展示了“一份很小的 handoff 文档”能有多大价值。Relay 保留这种轻量精神，但补上了工作流的另一半：

- `pass`：为下一个 agent 写一份 relay 文档。
- `pickup`：找到、读取并继续执行某份 relay 文档里的工作。
- 智能 `/relay`：自动判断用户是在递出接力棒，还是接到接力棒。
- 项目默认值：配置 Relay 文件写在哪里，以及默认写多详细。

当你同时使用多个 coding-agent 窗口、遇到上下文限制、临时暂停任务、切换模型，或者想让新 session 不必重新解释所有背景就能继续工作时，Relay 会很有用。

## 用法

### 1. 交棒

在一个繁忙 session 的末尾运行：

```text
/relay-pass
```

或者让 Relay 自动判断你是在交棒：

```text
/relay
```

Relay 会写出一个类似这样的 handoff 文档：

```text
.relay/relay-20260512T091530Z-exp3-reward-logging-a1b2c3.md
```

你也可以给下一个 session 留一个关注点：

```text
/relay-pass next session should continue experiment 3 and debug reward logging
```

### 2. 开启新 session 并接棒

在同一个项目里开启新的 coding-agent session，然后运行：

```text
/relay-pickup
```

或者：

```text
/relay
```

Relay 会找到最新的可能相关 handoff，读取它，说明自己使用了哪个文件，然后继续执行任务。

如果你知道要恢复哪条工作线，可以加一个 hint：

```text
/relay-pickup experiment 3 reward logging
```

如果你已经知道具体文件路径，可以直接传路径：

```text
/relay-pickup .relay/relay-20260512T091530Z-exp3-reward-logging-a1b2c3.md
```

### 3. 单次控制 pass 行为

当原话、决策或约束很重要时，写一份更详细的 handoff：

```text
/relay-pass --full preserve the important original wording and decisions
```

即使项目默认是详细版，也可以单次强制写精简版：

```text
/relay-pass --compact preserve only what the next session needs
```

单次强制写入项目内 `.relay/`：

```text
/relay-pass --keep next session should continue experiment 3
```

单次使用临时文件，兼容 Matt 风格的 temp 保存方式：

```text
/relay-pass --tmp next session should continue experiment 3
```

支持的单次参数：

- `--keep` / `--persist`：本次 handoff 写入 `.relay/`。
- `--tmp` / `--temp`：本次 handoff 写入 `${TMPDIR:-/tmp}`。
- `--full`：写详细版 handoff。
- `--compact` / `--brief`：写精简版 handoff。

### 4. 设置项目默认值

当你希望这个项目之后的 Relay 默认采用某种行为时，使用 `/relay-set`。

```text
/relay-set full temp
/relay-set compact project
/relay-set tmp
/relay-set full
```

这个语法刻意保持直接：输入的词就是默认值。

- `project`、`.relay`、`keep`、`persist`：默认写入 `.relay/`。
- `tmp`、`temp`、`/tmp`、`temporary`：默认写入 temp。
- `compact`、`brief`、`short`、`concise`：默认写精简版 handoff。
- `full`、`detailed`、`detail`：默认写详细版 handoff。

设置会保存在：

```text
.relay/config.json
```

没有配置文件时的内置默认值：

```json
{"storage":"project","detail":"compact"}
```

## Pickup 发现机制

Relay 会在两个位置寻找 handoff 候选：

- 当前项目的 `.relay/`。
- `${TMPDIR:-/tmp}` 的顶层，用于兼容 Matt 风格的 temp 文件。

候选文件名：

- `relay-*.md`：Relay 自己生成的文件。
- `handoff-*.md`：兼容 Matt 的 pickup 文件。

Relay 绝不能递归扫描共享临时目录。temp 发现应该是浅层的，例如：

```bash
find "${TMPDIR:-/tmp}" -maxdepth 1 -type f \( -name 'relay-*.md' -o -name 'handoff-*.md' \) -printf '%T@ %p\n' 2>/dev/null
```

这样可以避免递归 `rg` 或递归 `find /tmp` 时常见的 `/tmp/pymp-*`、`/tmp/tmp*wandb*` 权限错误。

## 安装

Relay 目前以普通 skill 文件和 command 文件发布。在 registry installer 发布之前，推荐安装方式是：

1. 把仓库 clone 到一个稳定的本地位置。
2. 把根目录 `skills/` 和 `commands/` 中的条目 symlink 到你的 agent 配置目录。
3. 重启 agent。

先 clone 一次：

```bash
mkdir -p ~/.local/share
git clone https://github.com/RiAnBee/relay-skill.git ~/.local/share/relay-skill
```

如果你已经 clone 到别的位置，把下面命令里的 `~/.local/share/relay-skill` 换成你的实际路径。

### Claude Code

Claude Code 在不同版本和 plugin 模式下支持的安装入口可能不同。如果你的 Claude Code 设置支持从本仓库进行 plugin 安装，优先使用 plugin 安装。否则使用手动安装。

手动 symlink 安装：

```bash
mkdir -p ~/.claude/skills ~/.claude/commands
ln -s ~/.local/share/relay-skill/skills/relay ~/.claude/skills/relay
ln -s ~/.local/share/relay-skill/skills/relay-pass ~/.claude/skills/relay-pass
ln -s ~/.local/share/relay-skill/skills/relay-pickup ~/.claude/skills/relay-pickup
ln -s ~/.local/share/relay-skill/skills/relay-set ~/.claude/skills/relay-set
ln -s ~/.local/share/relay-skill/commands/relay.md ~/.claude/commands/relay.md
ln -s ~/.local/share/relay-skill/commands/relay-pass.md ~/.claude/commands/relay-pass.md
ln -s ~/.local/share/relay-skill/commands/relay-pickup.md ~/.claude/commands/relay-pickup.md
ln -s ~/.local/share/relay-skill/commands/relay-set.md ~/.claude/commands/relay-set.md
```

fallback copy 安装：

```bash
mkdir -p ~/.claude/skills ~/.claude/commands
cp -R ~/.local/share/relay-skill/skills/relay* ~/.claude/skills/
cp ~/.local/share/relay-skill/commands/relay*.md ~/.claude/commands/
```

### Codex

Codex 支持优先使用 native skills。Relay 刻意不提供 Codex-specific prompt wrappers，因为根目录 `skills/` 是唯一 canonical 行为来源。

```bash
mkdir -p ~/.codex/skills
ln -s ~/.local/share/relay-skill/skills/relay ~/.codex/skills/relay
ln -s ~/.local/share/relay-skill/skills/relay-pass ~/.codex/skills/relay-pass
ln -s ~/.local/share/relay-skill/skills/relay-pickup ~/.codex/skills/relay-pickup
ln -s ~/.local/share/relay-skill/skills/relay-set ~/.codex/skills/relay-set
```

可以从 skill UI 触发，也可以用自然语言触发，例如：

```text
Use the relay-pass skill
Use the relay-pickup skill
Use the relay-set skill with full temp
```

### OpenCode

OpenCode 把 skills 和 slash commands 视为两套不同配置。为了获得最佳体验，请两者都安装。

任何时候都不要为了安装 Relay 删除、覆盖、替换已有项目 `.opencode` 目录。`.opencode` 是用户和项目自己的配置边界。

```bash
mkdir -p ~/.config/opencode/commands ~/.config/opencode/skills
ln -s ~/.local/share/relay-skill/commands/relay.md ~/.config/opencode/commands/relay.md
ln -s ~/.local/share/relay-skill/commands/relay-pass.md ~/.config/opencode/commands/relay-pass.md
ln -s ~/.local/share/relay-skill/commands/relay-pickup.md ~/.config/opencode/commands/relay-pickup.md
ln -s ~/.local/share/relay-skill/commands/relay-set.md ~/.config/opencode/commands/relay-set.md
ln -s ~/.local/share/relay-skill/skills/relay ~/.config/opencode/skills/relay
ln -s ~/.local/share/relay-skill/skills/relay-pass ~/.config/opencode/skills/relay-pass
ln -s ~/.local/share/relay-skill/skills/relay-pickup ~/.config/opencode/skills/relay-pickup
ln -s ~/.local/share/relay-skill/skills/relay-set ~/.config/opencode/skills/relay-set
```

不同 OpenCode 版本和 UI 对 project-local commands、GUI custom commands 的加载行为可能不同。Relay 文档化的 OpenCode 安装路径是全局 config，避免修改项目自有的 `.opencode` 目录。

## 如果 `/relay` 没有出现

如果安装成功但 `/relay` 没有出现在命令列表里：

1. 确认你已经为实际使用的 runtime 安装了根目录 `skills/`，并在 runtime 支持时安装了根目录 `commands/`。
2. 重启 runtime，让 skills 和 commands 被重新加载。
3. 检查 runtime 是否把 plugin skills 暴露成 namespaced commands。
4. 对 Codex，如果 slash commands 不可用，就通过 skill UI 或自然语言触发。
5. 对 OpenCode，优先使用全局 `~/.config/opencode/` 安装路径，而不是修改项目 `.opencode`。

这些 command wrappers 刻意保持很薄。它们的作用是在各 runtime 支持的范围内提供稳定用户入口，同时让 `skills/relay/SKILL.md` 继续作为唯一 canonical 行为定义。

## 包结构

Relay 使用“一套 canonical skills + 很薄的 command 入口”的结构：

```text
relay-skill/
├── .claude-plugin/plugin.json
├── commands/
│   ├── relay.md
│   ├── relay-pass.md
│   ├── relay-pickup.md
│   └── relay-set.md
├── skills/
│   ├── relay/SKILL.md
│   ├── relay-pass/SKILL.md
│   ├── relay-pickup/SKILL.md
│   └── relay-set/SKILL.md
└── adapters/
    ├── codex/README.md
    └── opencode/README.md
```

adapter 不再复制 skills 或 commands。所有 runtime 都安装同一套根目录 `skills/`；只有在 runtime 支持 slash-command 文件时，才额外安装根目录 `commands/`。

## Relay 文件与隐私

Relay 文档可能包含敏感项目上下文、私有文件路径、内部决策和用户原话。这同时适用于 `.relay/` 下的文件和 `${TMPDIR:-/tmp}` 下的临时文件。

本仓库的 `.gitignore` 默认忽略 `.relay/`，避免生成的 relay 文档被误提交。如果你确实想把 relay 文档纳入版本控制，请先审查内容，再从 `.gitignore` 中移除 `.relay/`。

不要在 relay 文档中提交 secrets、credentials、private tokens、客户数据或敏感内部信息。

## 致谢

Relay 受 Matt Pocock 在 [`mattpocock/skills`](https://github.com/mattpocock/skills) 中的 `handoff` skill 启发，并保留了部分核心措辞。原项目使用 MIT 许可证。

详情见 `NOTICE.md`。

## 许可证

MIT。见 `LICENSE`。
