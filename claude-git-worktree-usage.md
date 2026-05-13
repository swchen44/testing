# Claude Code Git Worktree 用法指南

本文档介绍如何在 Claude Code 中使用 git worktree（工作树），实现并行开发、隔离的子代理执行和大规模重构等高效工作流。

## 目录

- [什么是 Git Worktree](#什么是-git-worktree)
- [核心使用场景](#核心使用场景)
- [基础命令](#基础命令)
- [Claude Code 专属功能](#claude-code-专属功能)
- [配置选项](#配置选项)
- [最佳实践](#最佳实践)
- [常见陷阱](#常见陷阱)

---

## 什么是 Git Worktree

**Git worktree（工作树）** 是一个独立的工作目录，拥有自己的文件和分支，但与主仓库共享同一份历史记录和远程仓库。它允许你**同时检出多个分支**，而无需在本地切换。

Claude Code 对 worktree 提供**一等公民级**的原生支持：

- CLI 提供 `--worktree`（简写 `-w`）参数
- 子代理可通过 `isolation: "worktree"` 在隔离的工作树中运行
- Desktop 应用会为每个会话自动创建 worktree
- 默认存放路径：仓库根目录下的 `.claude/worktrees/<name>/`

---

## 核心使用场景

### 1. 并行功能开发

在同一仓库的不同分支上同时运行多个 Claude 会话，互不干扰：

```bash
# 终端 1：开发认证功能
claude --worktree feature-auth

# 终端 2：修复校验 bug
claude --worktree bugfix-validation

# 终端 3：监控所有会话
claude agents
```

### 2. 隔离的子代理执行

让并行的子代理在各自的 worktree 中工作，避免文件冲突：

```markdown
---
name: parallel-implementer
description: 在隔离环境中实现功能
isolation: worktree
---

你是一名实现专家，在分配的功能上独立工作……
```

### 3. 大规模重构（配合 `/batch`）

`/batch` 命令会将一项大型工作拆解为 5-30 个独立单元，每个单元在隔离的 worktree 中由后台子代理实现、测试并提交 PR。适合跨仓库的迁移或重构。

### 4. PR 专属工作

直接从一个 PR 创建 worktree 进行评审或修改：

```bash
claude --worktree "#1234"
claude --worktree "https://github.com/owner/repo/pull/1234"
```

---

## 基础命令

### 通过 Claude Code 创建（推荐）

```bash
# 创建命名的 worktree 并启动 Claude
claude --worktree feature-auth

# 创建匿名 worktree（Claude 自动生成名称，例如 "bright-running-fox"）
claude --worktree

# 基于 PR 创建
claude --worktree "#1234"
```

### 手动管理 Worktree

```bash
# 创建新 worktree 并新建分支
git worktree add ../project-feature-a -b feature-a

# 基于已有分支创建 worktree
git worktree add ../project-bugfix bugfix-123

# 列出所有 worktree
git worktree list

# 移除 worktree
git worktree remove ../project-feature-a

# 清理已删除目录的引用
git worktree prune
```

> **注意**：每个新 worktree 都是独立的检出，需要单独初始化开发环境（`npm install`、`python venv` 等）。

---

## Claude Code 专属功能

### 1. 子代理隔离参数

在 `.claude/agents/` 或 `~/.claude/agents/` 的子代理定义中加入 `isolation: worktree`：

```markdown
---
name: parallel-refactor
isolation: worktree
---
你在一个隔离的 worktree 中重构代码……
```

Agent SDK 中同样支持：

```python
AgentDefinition(
    description="功能实现者",
    prompt="实现分配的功能……",
    isolation="worktree"
)
```

### 2. `.worktreeinclude` 文件

在项目根目录创建 `.worktreeinclude`（语法类似 `.gitignore`），自动把被 gitignore 的文件复制到新建 worktree 中：

```text
.env
.env.local
config/secrets.json
```

> 只有**既匹配 `.worktreeinclude` 又被 gitignore** 的文件才会被复制，已跟踪的文件永远不会被重复。

### 3. Worktree 生命周期 Hooks

可在 `settings.json` 中配置：

```json
{
  "hooks": {
    "WorktreeCreate": [
      {
        "hooks": [
          { "type": "command", "command": "./scripts/setup-worktree.sh" }
        ]
      }
    ],
    "WorktreeRemove": [
      {
        "hooks": [
          { "type": "command", "command": "./scripts/cleanup-worktree.sh" }
        ]
      }
    ]
  }
}
```

这两个 hook 对使用非 git 版本控制（SVN、Perforce、Mercurial）的用户尤其重要。

---

## 配置选项

在 `.claude/settings.json` 中配置 worktree 行为：

```json
{
  "worktree": {
    "baseRef": "fresh",
    "symlinkDirectories": ["node_modules", ".cache"],
    "sparsePaths": ["packages/my-app", "shared/utils"]
  },
  "cleanupPeriodDays": 30
}
```

| 配置项 | 说明 |
|--------|------|
| `baseRef` | 新建 worktree 的基准引用。`"fresh"`（默认）= 基于 `origin/<default>` 创建干净的工作树；`"head"` = 基于本地 HEAD，可携带未推送的提交 |
| `symlinkDirectories` | 用软链接避免在每个 worktree 中重复占用大型目录（如 `node_modules`） |
| `sparsePaths` | 在大型 monorepo 中通过 git sparse-checkout 只检出指定路径 |
| `cleanupPeriodDays` | 自动清理超过该天数的孤立 worktree（默认 30 天） |

---

## 最佳实践

### 配置共享

- **CLAUDE.md 与 `.claude/` 自动共享**：所有 worktree 共用主仓库的项目级配置
- **`CLAUDE.local.md`** 被 gitignore，仅存在于单个 worktree 中
- **自动记忆**统一存放在 `~/.claude/projects/<project>/memory/`，跨 worktree 累积调试经验

跨 worktree 共享个人笔记：

```markdown
# 在 CLAUDE.md 中
- @~/.claude/my-project-instructions.md
```

### 命名与组织

- 使用有意义的名称：`feature-auth`、`bugfix-123`、`review-pr-456`
- 同时活跃的 worktree 建议保持在 **3-4 个以内**，过多会变得难以管理
- 一个 worktree 一项任务，副任务交给当前会话的子代理处理

### 上下文管理

- 每个 worktree 会话以全新的上下文窗口启动
- 频繁使用 `/clear` 释放上下文
- 使用 `/context` 查看 token 使用情况
- 将 CLAUDE.md 控制在 **200 行以内**，提升模型遵循度

### 清理流程

**自动清理**：当 worktree 没有未提交修改、未跟踪文件或新提交时，结束会话后会自动删除 worktree 和分支。

**手动清理**：

```bash
git worktree list
git worktree remove path/to/worktree
git worktree prune
```

**`.gitignore` 中加入**：

```
.claude/worktrees/
```

---

## 常见陷阱

### 1. 分支冲突
同一个分支不能在两个 worktree 中同时检出，否则会报：
```
fatal: 'branch-name' is already checked out in '/path/to/other-worktree'
```
**解决**：使用 `--worktree` 自动新建分支，或为每个 worktree 使用唯一分支名。

### 2. Stash 是共享的
Git stash 存放在对象库中，**跨 worktree 共享**；但工作目录状态不共享。在一个 worktree 中 stash，可能被另一个 worktree pop 出来，容易混淆。

### 3. 开发环境未初始化
新 worktree 是干净的检出，**不会自动继承已安装的依赖**。每个 worktree 需要单独：
- `npm install` / `pip install`
- 复制 `.env`（用 `.worktreeinclude`）
- 启动开发服务

### 4. 上下文污染
过大的 CLAUDE.md 或自动记忆会拖慢 worktree 启动。建议：
- CLAUDE.md 保持精简（< 200 行）
- 定期清理无关的自动记忆条目
- 任务切换时使用 `/clear`

### 5. 子代理过多导致评审遗漏
`/batch` 一次产生多个 PR 时，不要盲目合并——人工评审仍不可缺失。

### 6. 同时活跃的 worktree 过多
管理 10+ 个 worktree 容易出错。完成当前工作后及时清理，再开启新功能。

---

## 工作模式速查

| 模式 | 适用场景 | 文件隔离 | 协调方式 |
|------|----------|----------|----------|
| `--worktree` | 同一仓库的并行手动会话 | 各自目录与分支 | 用户协调 |
| 子代理 `isolation: worktree` | 当前会话内的并行子任务 | 临时独立 worktree | 结果汇总到父代理 |
| `/batch` | 仓库范围的大规模改动（5-30 单元） | 每个单元一个 worktree | 自动开 PR |
| Agent View (`claude agents`) | 监控多个后台会话 | 每个会话自动建 worktree | 集中仪表板 |

---

## 官方文档

- [Worktrees 完整指南](https://code.claude.com/docs/en/worktrees.md)
- [并行运行 Agent](https://code.claude.com/docs/en/agents.md)
- [Subagents](https://code.claude.com/docs/en/sub-agents.md)
- [Agent SDK Subagents](https://code.claude.com/docs/en/agent-sdk/subagents.md)
- [Memory 与 CLAUDE.md](https://code.claude.com/docs/en/memory.md)
- [Settings 设置](https://code.claude.com/docs/en/settings.md)
- [Hooks 参考](https://code.claude.com/docs/en/hooks.md)
