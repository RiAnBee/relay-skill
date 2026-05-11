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

## 安装

本仓库提供三层发现入口：

- `.claude-plugin/plugin.json`：让支持 plugin 的安装器发现 Relay skill。
- `commands/relay.md`：提供稳定的 `/relay` 命令 wrapper。
- `skills/relay/SKILL.md`：包含完整的 Relay 行为。

如果使用 Claude Code plugin 风格安装，请把本仓库作为 plugin 安装，让 `.claude-plugin/plugin.json` 注册 `skills/`。

如果手动安装 skill，请把这个目录复制到你的 coding agent 的 skills 目录：

```text
skills/relay/
```

如果手动安装 slash command，请把这个 command wrapper 复制到你的 coding agent 的 commands 目录：

```text
commands/relay.md
```

不同 coding agent 的 plugin、skill、command 目录可能不同。如果你的工具需要另一种目录结构，把 `skills/relay/SKILL.md` 和 `commands/relay.md` 复制到对应位置即可。

## 如果 `/relay` 没有出现

如果安装成功但 `/relay` 没有出现在命令列表里，说明你的运行时可能不会自动把 skill 暴露成 slash command。

可以用下面任一方式修复：

1. 把本仓库作为 Claude Code plugin 安装，让 `.claude-plugin/plugin.json` 被发现。
2. 手动把 `commands/relay.md` 复制到 commands 目录。
3. 手动把 `skills/relay/` 复制到 skills 目录，然后重启 agent runtime。

这个 command wrapper 刻意保持很薄。它的作用是让 `/relay` 拥有稳定的用户入口，即使不同 runtime 的 skill discovery 行为不一致。

## 用法

递出接力棒：

```text
/relay pass
```

递出接力棒，并告诉下一个 session 要关注什么：

```text
/relay pass next session should continue experiment 3 and debug reward logging
```

把 relay 文档持久化到项目内，而不是使用临时文件：

```text
/relay pass --keep next session should continue experiment 3
```

写一份更详细的 relay 文档：

```text
/relay pass --full preserve the important original wording and decisions
```

接起最新的可能相关 relay 文档：

```text
/relay pickup
```

接起某条具体工作线，并立即继续：

```text
/relay pickup continue experiment 3 and debug reward logging
```

让 Relay 自动判断动作：

```text
/relay
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
