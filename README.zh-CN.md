# Relay Skill

[EN](README.md) | 中文

Relay 是一个面向 coding agent 的轻量级 pass/pickup 接力 skill。

它以 Matt Pocock 出色的 [`handoff`](https://skills.sh/mattpocock/skills/handoff) skill 的精神和核心措辞为基础，并在此之上扩展了接棒能力、可选的项目内持久化、语义化文件名和详细模式。

## 为什么需要它

Matt Pocock 的 `handoff` skill 很擅长把当前对话压缩成一份 handoff 文档，让另一个 agent 能继续工作。

Relay 保留这种轻量设计，但补上工作流的另一半：

- `pass`：为下一个 agent 写一份 relay 文档。
- `pickup`：找到、读取并继续执行某份 relay 文档里的工作。
- 智能 `/relay`：自动判断用户现在是在递出接力棒，还是接到接力棒。

当你同时使用多个 coding-agent 窗口、遇到上下文限制、临时暂停任务，或者想让新 session 不必重新解释所有背景就能继续工作时，它会很有用。

## 包结构

Relay 使用“核心 skill + 平台 adapter”的结构：

- `skills/relay/SKILL.md`：Relay 的智能 canonical 行为定义。
- `skills/relay-pass/SKILL.md`：显式 pass 模式行为。
- `skills/relay-pickup/SKILL.md`：显式 pickup 模式行为。
- `.claude-plugin/plugin.json`：Claude Code plugin metadata。
- `commands/`：Claude Code slash-command wrappers。
- `adapters/codex/`：Codex skills 和 prompt-command fallback。
- `adapters/opencode/`：OpenCode `skills/` 和 `commands/` wrappers。

这些 adapter 都刻意保持很薄。它们会指回 canonical Relay skill，而不是复制产品行为。

## 安装：Claude Code

本仓库提供三层发现入口：

- `.claude-plugin/plugin.json`：让支持 plugin 的安装器发现 Relay skill。
- `commands/`：提供 `/relay`、`/relay-pass`、`/relay-pickup` 命令 wrappers。
- `skills/`：包含 Relay 行为 skills。

如果使用 Claude Code plugin 风格安装，请把本仓库作为 plugin 安装，让 `.claude-plugin/plugin.json` 注册这个包。

如果手动安装 skill，请把 skill 目录复制到 Claude skills 目录：

```bash
mkdir -p ~/.claude/skills
cp -R skills/relay skills/relay-pass skills/relay-pickup ~/.claude/skills/
```

如果手动安装 slash command，请把 command wrappers 复制到 Claude commands 目录：

```bash
mkdir -p ~/.claude/commands
cp commands/relay*.md ~/.claude/commands/
```

不同 Claude Code 版本和安装模式可能会把 plugin skills 暴露成 namespaced commands。如果你把 Relay 作为 plugin 安装，请同时检查 `/relay` 以及 slash-command 菜单里显示的 namespaced Relay 入口。

## 安装：Codex

Codex 非常重要，所以这里优先使用 Codex native skills。Custom prompts 只作为显式 slash-command fallback。

安装 Codex skills：

```bash
mkdir -p ~/.codex/skills
cp -R adapters/codex/skills/relay adapters/codex/skills/relay-pass adapters/codex/skills/relay-pickup ~/.codex/skills/
```

然后重启 Codex 或开启新的 Codex session。你可以从 Codex 的 skill UI 触发，或用自然语言触发，例如 `Use the relay-pass skill`。

如果需要显式 custom-prompt fallback commands，复制：

```bash
mkdir -p ~/.codex/prompts
cp adapters/codex/prompts/relay*.md ~/.codex/prompts/
```

然后使用 `/prompts:relay`、`/prompts:relay-pass` 或 `/prompts:relay-pickup`。

详见 `adapters/codex/README.md`。

## 安装：OpenCode

OpenCode 把 skills 和 slash commands 视为两套不同配置。

任何时候都不要为了安装 Relay 删除、覆盖、替换已有 `.opencode`。`.opencode` 是用户和项目自己的配置边界。

如果要全局安装，可以把根目录的 `commands/` 和 `skills/` 条目复制或 symlink 到 OpenCode config：

```bash
mkdir -p ~/.config/opencode/commands ~/.config/opencode/skills
ln -s /path/to/relay-skill/commands/relay.md ~/.config/opencode/commands/relay.md
ln -s /path/to/relay-skill/commands/relay-pass.md ~/.config/opencode/commands/relay-pass.md
ln -s /path/to/relay-skill/commands/relay-pickup.md ~/.config/opencode/commands/relay-pickup.md
ln -s /path/to/relay-skill/skills/relay ~/.config/opencode/skills/relay
ln -s /path/to/relay-skill/skills/relay-pass ~/.config/opencode/skills/relay-pass
ln -s /path/to/relay-skill/skills/relay-pickup ~/.config/opencode/skills/relay-pickup
```

`adapters/opencode/` 目录是给只想复制 OpenCode-specific 子集的用户准备的。

为了让 OpenCode 发现 adapter skills，复制到全局 OpenCode skills 目录：

```bash
mkdir -p ~/.config/opencode/skills
cp -R adapters/opencode/skills/relay adapters/opencode/skills/relay-pass adapters/opencode/skills/relay-pickup ~/.config/opencode/skills/
```

为了获得显式 `/relay*` commands，复制到全局 OpenCode commands 目录：

```bash
mkdir -p ~/.config/opencode/commands
cp adapters/opencode/commands/relay*.md ~/.config/opencode/commands/
```

不同 OpenCode 版本和 UI 对 project-local commands、GUI custom commands 的加载行为可能不同。Relay 文档化的 OpenCode 安装路径是全局 config，避免修改项目自有的 `.opencode` 目录。

详见 `adapters/opencode/README.md`。

## 如果 `/relay` 没有出现

如果安装成功但 `/relay` 没有出现在命令列表里，说明你的运行时可能不会自动把 skill 暴露成 slash command。

可以用下面任一方式修复：

1. 确认你安装的是当前 agent runtime 对应的 adapter。
2. 重启 runtime，让 skills、prompts 或 commands 被重新加载。
3. 对 Claude Code，尝试 plugin install，或手动复制所有 `commands/relay*.md` 和 `skills/relay*/` 条目。
4. 对 Codex，优先安装 `adapters/codex/skills/relay*/`；`/prompts:relay*` 只作为 fallback。
5. 对 OpenCode，把所有 `relay*` skill 和 command adapter 安装到全局 `~/.config/opencode/commands/` 和 `~/.config/opencode/skills/`。

这些 command wrappers 刻意保持很薄。它们的作用是在各 runtime 支持的范围内提供稳定用户入口，同时让 `skills/relay/SKILL.md` 继续作为唯一 canonical 行为定义。

## 用法

智能模式，自动判断 pass 或 pickup：

```text
/relay
```

不需要手动输入 subcommand，直接递出接力棒：

```text
/relay-pass
```

递出接力棒，并告诉下一个 session 要关注什么：

```text
/relay-pass next session should continue experiment 3 and debug reward logging
```

把 relay 文档持久化到项目内，而不是使用临时文件：

```text
/relay-pass --keep next session should continue experiment 3
```

写一份更详细的 relay 文档：

```text
/relay-pass --full preserve the important original wording and decisions
```

接起最新的可能相关 relay 文档：

```text
/relay-pickup
```

接起某条具体工作线，并立即继续：

```text
/relay-pickup continue experiment 3 and debug reward logging
```

## 默认行为

- 默认使用临时 relay 文件。
- 只有在用户使用 `--keep`、`--persist` 或明确自然语言要求时，才写入持久化 `.relay/` 文件。
- 文件名格式：`relay-<UTC timestamp>-<semantic slug>-<random suffix>.md`。
- Markdown 章节是条件型的：宁可省略泛泛内容，也不要编造下一步、blocker、风险或开放问题。
- 已存在的 artifacts 只通过路径或 URL 引用，不复制正文。

## 持久文件与隐私

Relay 文档可能包含敏感项目上下文、私有文件路径、内部决策和用户原话。

本仓库的 `.gitignore` 默认忽略 `.relay/`，避免生成的 relay 文档被误提交。如果你确实想把 relay 文档纳入版本控制，请先审查内容，再从 `.gitignore` 中移除 `.relay/`。

不要在 relay 文档中提交 secrets、credentials、private tokens、客户数据或敏感内部信息。

## 致谢

Relay 受 Matt Pocock 在 [`mattpocock/skills`](https://github.com/mattpocock/skills) 中的 `handoff` skill 启发，并保留了部分核心措辞。原项目使用 MIT 许可证。

详情见 `NOTICE.md`。

## 许可证

MIT。见 `LICENSE`。
