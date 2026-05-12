# Relay Skill

[EN](README.md) | 中文

Relay 是一个面向 coding agent 的轻量级 pass/pickup 接力 skill。

它以 Matt Pocock 出色的 [`handoff`](https://skills.sh/mattpocock/skills/handoff) skill 的精神和核心措辞为基础，并在此之上扩展了接棒能力、可配置默认保存位置、语义化文件名和详细模式。

## 为什么需要它

Matt Pocock 的 `handoff` skill 很擅长把当前对话压缩成一份 handoff 文档，让另一个 agent 能继续工作。

Relay 保留这种轻量设计，但补上工作流的另一半：

- `pass`：为下一个 agent 写一份 relay 文档。
- `pickup`：找到、读取并继续执行某份 relay 文档里的工作。
- 智能 `/relay`：自动判断用户现在是在递出接力棒，还是接到接力棒。

当你同时使用多个 coding-agent 窗口、遇到上下文限制、临时暂停任务，或者想让新 session 不必重新解释所有背景就能继续工作时，它会很有用。

## 包结构

Relay 使用“一套 canonical skills + 很薄的 command 入口”的结构：

- `skills/relay/SKILL.md`：Relay 的智能 canonical 行为定义。
- `skills/relay-pass/SKILL.md`：显式 pass 模式行为。
- `skills/relay-pickup/SKILL.md`：显式 pickup 模式行为。
- `skills/relay-set/SKILL.md`：项目级 Relay 默认设置。
- `.claude-plugin/plugin.json`：Claude Code plugin metadata。
- `commands/`：给支持 command 文件的 runtime 使用的薄 slash-command wrappers。
- `adapters/codex/`：只保留 Codex 安装说明。
- `adapters/opencode/`：只保留 OpenCode 安装说明。

adapter 不再复制 skills 或 commands。所有 runtime 都安装同一套根目录 `skills/`；只有在 runtime 支持 slash-command 文件时，才额外安装根目录 `commands/`。

## 安装：Claude Code

本仓库提供三层发现入口：

- `.claude-plugin/plugin.json`：让支持 plugin 的安装器发现 Relay skill。
- `commands/`：提供 `/relay`、`/relay-pass`、`/relay-pickup`、`/relay-set` 命令 wrappers。
- `skills/`：包含 Relay 行为 skills。

如果使用 Claude Code plugin 风格安装，请把本仓库作为 plugin 安装，让 `.claude-plugin/plugin.json` 注册这个包。

如果手动安装 skill，请把 skill 目录复制到 Claude skills 目录：

```bash
mkdir -p ~/.claude/skills
cp -R skills/relay skills/relay-pass skills/relay-pickup skills/relay-set ~/.claude/skills/
```

如果手动安装 slash command，请把 command wrappers 复制到 Claude commands 目录：

```bash
mkdir -p ~/.claude/commands
cp commands/relay*.md ~/.claude/commands/
```

不同 Claude Code 版本和安装模式可能会把 plugin skills 暴露成 namespaced commands。如果你把 Relay 作为 plugin 安装，请同时检查 `/relay` 以及 slash-command 菜单里显示的 namespaced Relay 入口。

## 安装：Codex

Codex 非常重要，所以这里优先使用 Codex native skills。Relay 不再维护 Codex-specific skill 副本或 prompt-command wrappers；根目录 `skills/` 是唯一 canonical 安装来源。

安装 Codex skills：

```bash
mkdir -p ~/.codex/skills
cp -R skills/relay skills/relay-pass skills/relay-pickup skills/relay-set ~/.codex/skills/
```

然后重启 Codex 或开启新的 Codex session。你可以从 Codex 的 skill UI 触发，或用自然语言触发，例如 `Use the relay-pass skill` 或 `Use the relay-set skill`。

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
ln -s /path/to/relay-skill/commands/relay-set.md ~/.config/opencode/commands/relay-set.md
ln -s /path/to/relay-skill/skills/relay ~/.config/opencode/skills/relay
ln -s /path/to/relay-skill/skills/relay-pass ~/.config/opencode/skills/relay-pass
ln -s /path/to/relay-skill/skills/relay-pickup ~/.config/opencode/skills/relay-pickup
ln -s /path/to/relay-skill/skills/relay-set ~/.config/opencode/skills/relay-set
```

不同 OpenCode 版本和 UI 对 project-local commands、GUI custom commands 的加载行为可能不同。Relay 文档化的 OpenCode 安装路径是全局 config，避免修改项目自有的 `.opencode` 目录。

详见 `adapters/opencode/README.md`。

## 如果 `/relay` 没有出现

如果安装成功但 `/relay` 没有出现在命令列表里，说明你的运行时可能不会自动把 skill 暴露成 slash command。

可以用下面任一方式修复：

1. 确认你已经安装根目录 `skills/`，并在 runtime 支持时安装根目录 `commands/`。
2. 重启 runtime，让 skills、prompts 或 commands 被重新加载。
3. 对 Claude Code，尝试 plugin install，或手动复制所有 `commands/relay*.md` 和 `skills/relay*/` 条目。
4. 对 Codex，安装根目录 `skills/relay*/`，然后通过 skill UI 或自然语言触发。
5. 对 OpenCode，把根目录 `skills/relay*/` 和 `commands/relay*.md` 安装到全局 `~/.config/opencode/`。

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

单次强制使用项目内 `.relay/` 保存：

```text
/relay-pass --keep next session should continue experiment 3
```

单次强制使用临时文件，兼容 Matt 风格的 temp 保存方式：

```text
/relay-pass --tmp next session should continue experiment 3
```

写一份更详细的 relay 文档：

```text
/relay-pass --full preserve the important original wording and decisions
```

即使项目默认是详细版，也单次强制写精简版：

```text
/relay-pass --compact preserve only what the next session needs
```

接起最新的可能相关 relay 文档：

```text
/relay-pickup
```

接起某条具体工作线，并立即继续：

```text
/relay-pickup continue experiment 3 and debug reward logging
```

用直接词语设置项目默认行为：

```text
/relay-set full temp
/relay-set compact project
/relay-set tmp
/relay-set full
```

## 默认行为

- 内置默认保存位置是项目内 `.relay/`。
- 内置默认详细程度是精简版 compact。
- 项目默认值保存在 `.relay/config.json`，可以通过 `/relay-set` 修改。
- 使用 `--keep` 或 `--persist` 可以单次强制写入 `.relay/`。
- 使用 `--tmp` 或 `--temp` 可以单次强制写入 `${TMPDIR:-/tmp}`。
- 使用 `--full` 可以单次强制写详细版。
- 使用 `--compact` 或 `--brief` 可以单次强制写精简版。
- 文件名格式：`relay-<UTC timestamp>-<semantic slug>-<random suffix>.md`。
- pickup 会在 `.relay/` 和 `${TMPDIR:-/tmp}` 顶层寻找 `relay-*.md` 以及兼容 Matt 的 `handoff-*.md` 候选，然后选择最新的可能匹配。
- pickup 绝不能递归扫描 `/tmp`、`$TMPDIR` 这类共享临时目录。
- Markdown 章节是条件型的：宁可省略泛泛内容，也不要编造下一步、blocker、风险或开放问题。
- 已存在的 artifacts 只通过路径或 URL 引用，不复制正文。

## Relay 文件与隐私

Relay 文档可能包含敏感项目上下文、私有文件路径、内部决策和用户原话。这同时适用于 `.relay/` 下的文件和 `${TMPDIR:-/tmp}` 下的临时文件。

本仓库的 `.gitignore` 默认忽略 `.relay/`，避免生成的 relay 文档被误提交。如果你确实想把 relay 文档纳入版本控制，请先审查内容，再从 `.gitignore` 中移除 `.relay/`。

不要在 relay 文档中提交 secrets、credentials、private tokens、客户数据或敏感内部信息。

## 致谢

Relay 受 Matt Pocock 在 [`mattpocock/skills`](https://github.com/mattpocock/skills) 中的 `handoff` skill 启发，并保留了部分核心措辞。原项目使用 MIT 许可证。

详情见 `NOTICE.md`。

## 许可证

MIT。见 `LICENSE`。
