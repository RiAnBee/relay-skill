# Relay Skill

<p align="center">
  <img src="./assets/relay-skill-banner.png" alt="relay-skill banner" width="100%" />
</p>

[EN](README.md) | 中文

Relay 是一个面向 coding agent 的轻量级 pass/pickup 接力 skill。

它帮助你干净地结束一个已经很拥挤的 session，开启一个新的 session，并且不用手动重写所有上下文就能继续同一项工作。

Relay 仍然保留 Matt Pocock 原始 `handoff` 的轻量精神，但把真正容易出问题的两个地方加强了：

- 默认 handoff 文档更结构化、更不容易被误读
- pickup 选文件时更谨慎、更不容易接错

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
- Relay 默认写 compact handoff，但这个 compact 模式仍然应该是结构化、高信号的。
- `--full` 是最大保真模式。它应该不在乎 token 成本，优先保证接力质量。
- 智能 `/relay` 仍然保留，但在一个 fresh 且信号模糊的 session 里，Relay 应该优先问一句短问题，而不是静默加载某个旧 handoff。
- `.relay/` 会被本仓库的 `.gitignore` 规则忽略；除非你明确要版本化，否则应把它当作本地工作状态。

## 为什么需要它

现在的 coding-agent 工作流早已不只是一个聊天框。很多开发者会在 `.claude/`、`.opencode/` 或全局 skill 目录里维护自己的个性化 harness。项目里也常常会有 `CLAUDE.md`、`AGENTS.md`、rules、playbooks 等文件；这些内容会在每个 session 开始时自动注入，让 agent 一开始就拿到正确的运行上下文。

这在 session 刚开始时很好用。问题通常出现在后半段：当一个 session 已经经历了很多轮对话、很长的工具输出、失败的探索、局部计划和微妙决策之后，你仍然想基于当前状态继续工作。最自然的做法是 compact 当前 session 然后继续。但这取决于具体 runtime 的设计：自动注入的信息可能被压缩或模糊化，session 管理也不够优雅、不易追溯，一些重要细节可能丢失，最终影响输出质量。

另一个办法是新开 session，然后手动写一段精心整理的 prompt 描述当前情况。这通常是更好的工程卫生，但非常消耗心神。你需要记住改过什么、哪里失败了、哪些约束重要、下一个 agent 应该先做什么。

Relay 就是为这个空隙而生的：把接力棒从一个 session 传给下一个 session。

Matt Pocock 出色的 [`handoff`](https://skills.sh/mattpocock/skills/handoff) skill 展示了“一份很小的 handoff 文档”能有多大价值。Relay 保留这种轻量精神，但补上了工作流的另一半，并加强了默认接力质量：

- `pass`：为下一个 agent 写一份 relay 文档。
- `pickup`：找到、读取、校验并继续执行某份 relay 文档里的工作。
- 智能 `/relay`：自动判断用户是在递出接力棒还是接到接力棒，但避免在 fresh 模糊场景里静默误接。
- 项目默认值：配置 Relay 文件写在哪里，以及默认写多详细。

当你同时使用多个 coding-agent 窗口、遇到上下文限制、临时暂停任务、切换模型，或者想让新 session 不必重新解释所有背景就能继续工作时，Relay 会很有用。

## Relay 加强了什么

Relay 不是想把 Matt 的想法换成另一套更重的系统，而是在保持骨架不变的前提下，加强真实使用里最容易失手的点。

### 更强的默认 pass

默认 handoff 仍然是 compact，但它应该优先保住这些最容易丢失的信息：

- 真正目标是什么
- 哪些硬约束不能被破坏
- 当前做到哪一步了
- 哪些路线已经试过且不要重试
- 哪些决策已经定下来了
- 下一步最该先做什么

### 更强的默认 pickup

pickup 不应该只是拿最新文件赌运气。它应该优先使用这些信号来选最合适的 relay：

- 显式文件路径
- 文件名或 slug 匹配
- 用户给出的 hint 或 focus
- branch 或 working directory 匹配
- 时间新旧

pickup 也应该明确告诉用户它使用了哪个 relay 文件，并在 handoff 看起来 stale 或不匹配时做简短提醒。

### 更强的 `--full`

`--full` 不是“稍微长一点”，而是真正的最大保真模式：

- 保留更多用户原话
- 保留更多决策理由
- 保留死路和失败原因
- 保留更多文件与 workspace 上下文
- 给下一个 agent 更强的重启提示

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

### 2. 默认 Relay 文档长什么样

Relay 现在更偏好使用 YAML frontmatter 加结构化 Markdown 正文：

```markdown
---
schema_version: 1
created: 2026-06-03T09:15:30Z
mode: compact
storage: project
working_directory: /repo
focus: experiment 3 reward logging
branch: main
commit: a1b2c3d
---

# Relay: experiment 3 reward logging

## Goal

Continue experiment 3 and fix reward logging without reopening the storage design.

## Hard Constraints

- Do not change the experiment naming scheme.
- Keep the current log format backward-compatible.

## Current State

Reward logging was traced to the wrapper layer. Two files were already edited and tests were not rerun yet.

## Failed Approaches

- Rewriting the entire logging adapter was too broad for the bug and introduced unrelated churn.

## Explicit Next Step

Inspect the wrapper call site, patch the missing reward field, then rerun the targeted tests.

## References

- `src/wrapper.py`: likely source of the missing reward field.
- `tests/test_reward_logging.py`: targeted regression coverage.
```

当某个 section 存在时，尽量使用固定标题名。因为 fresh agent 最容易丢掉的，往往就是约束、失败路径和已经定下的决定。

### 3. 可直接复制的 compact 模板

当你想要结构化、高信号，但又不想付出 `--full` 的 token 成本时，可以直接参考这个模板：

```markdown
---
schema_version: 1
created: 2026-06-03T09:15:30Z
mode: compact
storage: project
working_directory: /path/to/project
focus: <next-session focus>
branch: <branch-if-known>
commit: <commit-if-known>
---

# Relay: <short title>

## Goal

<What the next session is trying to achieve.>

## Hard Constraints

- <Constraint that must not be violated>
- <Another hard boundary>

## Current State

<Known current state only. No guesses.>

## Failed Approaches

- <What was tried and why the next session should not repeat it>

## Settled Decisions

- <Decision already made and not meant to be casually reopened>

## Explicit Next Step

<Best first action for the next agent>

## References

- `<path-or-url>`: <why it matters>
```

### 4. 可直接复制的 full 模板

当你要追求“极致接力”时，可以把 `--full` 按这个形态去写：

```markdown
---
schema_version: 1
created: 2026-06-03T09:15:30Z
mode: full
storage: project
working_directory: /path/to/project
focus: <next-session focus>
branch: <branch-if-known>
commit: <commit-if-known>
---

# Relay: <short title>

## Goal

<What the work is trying to achieve, written for a zero-context agent.>

## Hard Constraints

- <Exact wording or close paraphrase of the constraints that must survive>
- <Performance, compatibility, or scope boundaries>

## Current State

<Where things stand now, including useful validation status or workspace facts when known.>

## Failed Approaches

- <Approach that failed>
  Why it failed: <brief reason>

这里应优先记录真正有价值的产品、设计、实现或调查死路，而不是价值很低的流程小故障。只有当流程问题会影响下一棒时，才值得写进去。

## Settled Decisions

- <Decision already made>
  Why it was made: <brief rationale>

## Verbatim Doctrine

- "<下一棒应尽量原样继承的重要用户原话>"

## Explicit Next Step

<下一棒最该先做的唯一动作；如果任务已完成，就直接写明无需继续>

## Known Blockers

- <Only include real blockers>

## Open Questions

- <Only include unresolved questions that truly matter>

## Files Changed

- `<path>`: <what changed>

## Files Consulted

- `<path>`: <why it mattered>

## Suggested Skills

- `<skill>`: <why the next session should use it>

## References

- `<path-or-url>`: <why it matters>

## Resume Prompt

Continue from this relay. Start by <first action>. Preserve the hard constraints above, do not repeat the failed approaches, and use the referenced files before widening scope.
```

### 5. 开启新 session 并接棒

在同一个项目里开启新的 coding-agent session，然后运行：

```text
/relay-pickup
```

或者：

```text
/relay
```

Relay 理想上应该：

1. 先看 `.relay/`
2. 如果你给了 hint，就优先用 hint
3. 尽量选最合适的候选，而不是盲目选最新文件
4. 明确说明它用了哪个文件
5. 如果 relay 看起来 stale 或不匹配，先提醒一句
6. 然后继续执行任务

如果你知道要恢复哪条工作线，可以加一个 hint：

```text
/relay-pickup experiment 3 reward logging
```

如果你已经知道具体文件路径，可以直接传路径：

```text
/relay-pickup .relay/relay-20260512T091530Z-exp3-reward-logging-a1b2c3.md
```

智能 `/relay` 仍然保留，但 Relay 不应该在一个 fresh 且模糊的 session 里静默自动 pickup 某个旧 handoff。信号弱时，先问一句短问题，比“自信地接错”更好。

### 6. 用 `--full` 做极致接力

当原话、决策、权衡或死路都很重要时，写一份更完整的 handoff：

```text
/relay-pass --full preserve the important original wording and decisions
```

在 `--full` 模式里，Relay 应该优先追求接力质量，而不是节省 token。一个 full relay 通常应该在这些部分保留更多细节：

- `Hard Constraints`
- `Current State`
- `Failed Approaches`
- `Settled Decisions`
- `Verbatim Doctrine`
- `Files Changed`
- `Files Consulted`
- `References`
- `Resume Prompt`

即使在 `--full` 下，Relay 仍然不应该无脑复制大段 artifact。除非“原文”本身就是必须保留的东西，否则优先按 path 或 URL 引用。

`--full` 真正应该增强的，不只是“更多行数”，而是：保留更多用户 doctrine 原话、把下一步收敛成单一起步动作、并记录最有价值的不可重试死路。

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
- `--full`：写最大保真 handoff。
- `--compact` / `--brief`：写 compact handoff。

### 7. 设置项目默认值

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
- `compact`、`brief`、`short`、`concise`：默认写 compact handoff。
- `full`、`detailed`、`detail`：默认写 full handoff。

设置会保存在：

```text
.relay/config.json
```

没有配置文件时的内置默认值：

```json
{"storage":"project","detail":"compact"}
```

常见的 `relay-set` 组合：

- `/relay-set compact project`：最适合日常使用的默认值。
- `/relay-set full project`：适合你希望所有常规 relay 都偏向高保真的场景。
- `/relay-set compact temp`：最接近 Matt 风格的一次性 handoff。
- `/relay-set full temp`：详细但一次性的 relay 文件。

## Pickup 发现机制

Relay 会在两个位置寻找 handoff 候选：

- 当前项目的 `.relay/`。
- `${TMPDIR:-/tmp}` 的顶层，用于兼容 Matt 风格的 temp 文件。

候选文件名：

- `relay-*.md`：Relay 自己生成的文件。
- `handoff-*.md`：兼容 Matt 的 pickup 文件。

Relay 绝不能递归扫描共享临时目录。temp 发现应该是浅层的，例如：

```bash
find "${TMPDIR:-/tmp}" -maxdepth 1 -type f \( -name 'relay-*.md' -o -name 'handoff-*.md' \) -print 2>/dev/null
```

```bash
find .relay -maxdepth 1 -type f \( -name 'relay-*.md' -o -name 'handoff-*.md' \) -print 2>/dev/null
```

这样可以避免递归 `rg` 或递归 `find /tmp` 时常见的 `/tmp/pymp-*`、`/tmp/tmp*wandb*` 权限错误。

当有良好 metadata 时，Relay 应优先使用 `created` 时间和文件名里的时间戳，而不是单纯依赖 mtime 猜测。

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

## Validation Fixtures

这个仓库现在带了一套轻量 fixture 和契约检查脚本，用来验证文档里声明的 relay 格式。

运行：

```bash
python tests/check_relay_contracts.py
```

脚本会检查：

- 加强后的 `skills/relay/SKILL.md` 契约
- README 模板 section 是否齐全
- compact、full、legacy pickup 三类 fixture 文件

## Relay 文件与隐私

Relay 文档可能包含敏感项目上下文、私有文件路径、内部决策和用户原话。这同时适用于 `.relay/` 下的文件和 `${TMPDIR:-/tmp}` 下的临时文件。

应把 `.relay/` 视为优先存储位置。temp 文件更多是兼容性导向，通常也更不私密。

Relay 应避免把明显的 secrets、tokens、private keys、passwords 或客户数据复制进 handoff 文档。如果原话里确实包含敏感值但又必须保留语义，请把值 redact 掉，并说明做过 redaction。

本仓库的 `.gitignore` 默认忽略 `.relay/`，避免生成的 relay 文档被误提交。如果你确实想把 relay 文档纳入版本控制，请先审查内容，再从 `.gitignore` 中移除 `.relay/`。

不要在 relay 文档中提交 secrets、credentials、private tokens、客户数据或敏感内部信息。

## 致谢

Relay 受 Matt Pocock 在 [`mattpocock/skills`](https://github.com/mattpocock/skills) 中的 `handoff` skill 启发，并保留了部分核心措辞。原项目使用 MIT 许可证。

详情见 `NOTICE.md`。

## 许可证

MIT。见 `LICENSE`。
