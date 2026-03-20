# Multi-Agent Workflow System — 設計書

**文件版本**：v1.0
**狀態**：Draft
**依據**：agents-requirements.md v1.0

---

## 1. 系統架構總覽

```mermaid
graph TB
    subgraph Claude Code Runtime
        direction TB

        subgraph Entry Layer
            FA[Featured Agent\nSOUL + DUTIES + MEMORY]
        end

        subgraph Agent Layer
            FT[Fetcher Agent]
            FX[Fixer Agent]
            DV[Developer Agent]
        end

        subgraph Skill Layer
            subgraph Shared Skills 共用技能庫
                SC[.claude/skills/\nproject-context/\ngit-operations/\nbuild-systems/\nhandoff-protocol/]
            end
            subgraph Private Skills 私有技能
                FS[fetcher/skills/\nbuild-advanced/]
                FXS[fixer/skills/\nerror-patterns/]
                DS[developer/skills/\nfeature-patterns/]
            end
        end

        subgraph Memory Layer
            SM[memory/shared/\nproject.md\nconventions.md\ndecisions.md]
            WM[memory/agents/\nfetcher/working.md\nfixer/working.md\ndeveloper/working.md]
            HM[memory/handoffs/\nrun-id/\n01-fetcher.md\n02-fixer.md]
        end
    end

    subgraph Infrastructure
        GIT[(Git Repository)]
        CFG[.claude/agent-config.json]
        REG[agents/registry.json]
    end

    FA -->|偵測需求| FT & FX & DV
    FT & FX & DV -->|symlink| SC
    FT -->|私有| FS
    FX -->|私有| FXS
    DV -->|私有| DS
    FT & FX & DV --> SM & WM
    FT & FX & DV -->|交接時寫入| HM
    HM -->|git commit| GIT
    SM -->|git commit| GIT
    CFG -->|控制行為| FA & FT & FX & DV
    REG -->|Agent 目錄| FA
```

---

## 2. 目錄結構設計

```
project-root/
│
├── CLAUDE.md                          ← 全域背景，@引用共用技能
│
├── .claude/
│   ├── settings.json                  ← Hooks 設定
│   ├── agent-config.json              ← 使用者行為設定
│   └── skills/                        ← 共用技能庫（真實檔案）
│       ├── project-context/
│       │   └── SKILL.md
│       ├── git-operations/
│       │   └── SKILL.md
│       ├── build-systems/
│       │   └── SKILL.md
│       ├── code-reading/
│       │   └── SKILL.md
│       └── handoff-protocol/
│           └── SKILL.md
│
├── agents/
│   ├── registry.json                  ← Agent 目錄與安裝資訊
│   │
│   ├── featured/                      ← 必裝，入口 Agent
│   │   ├── CLAUDE.md                  ← 按需載入 featured 技能
│   │   ├── SOUL.md                    ← 身份定義
│   │   ├── DUTIES.md                  ← 職責與交接程序
│   │   └── skills/
│   │       ├── project-context  ──symlink──► .claude/skills/project-context/
│   │       ├── git-operations   ──symlink──► .claude/skills/git-operations/
│   │       ├── handoff-protocol ──symlink──► .claude/skills/handoff-protocol/
│   │       └── agent-discovery/       ← featured 私有技能
│   │           └── SKILL.md
│   │
│   ├── fetcher/                       ← 選裝
│   │   ├── CLAUDE.md
│   │   ├── SOUL.md
│   │   ├── DUTIES.md
│   │   └── skills/
│   │       ├── project-context  ──symlink──►
│   │       ├── git-operations   ──symlink──►
│   │       ├── build-systems    ──symlink──►
│   │       ├── handoff-protocol ──symlink──►
│   │       └── build-advanced/        ← fetcher 私有技能
│   │           └── SKILL.md
│   │
│   ├── fixer/                         ← 選裝
│   │   ├── CLAUDE.md
│   │   ├── SOUL.md
│   │   ├── DUTIES.md
│   │   └── skills/
│   │       ├── project-context  ──symlink──►
│   │       ├── code-reading     ──symlink──►
│   │       ├── handoff-protocol ──symlink──►
│   │       └── error-patterns/
│   │           └── SKILL.md
│   │
│   └── developer/                     ← 選裝
│       ├── CLAUDE.md
│       ├── SOUL.md
│       ├── DUTIES.md
│       └── skills/
│           ├── project-context  ──symlink──►
│           ├── code-reading     ──symlink──►
│           ├── handoff-protocol ──symlink──►
│           └── feature-patterns/
│               └── SKILL.md
│
├── memory/
│   ├── shared/                        ← 所有 Agent 共用，Git 追蹤
│   │   ├── project.md
│   │   ├── conventions.md
│   │   └── decisions.md
│   ├── agents/
│   │   ├── featured/working.md        ← 各 Agent 工作記憶（交接後清除）
│   │   ├── fetcher/working.md
│   │   ├── fixer/working.md
│   │   └── developer/working.md
│   └── handoffs/                      ← 壓縮交接摘要，Git 追蹤
│       └── {run-id}/
│           ├── 01-fetcher.md
│           ├── 02-fixer.md
│           └── 03-developer.md
│
└── scripts/
    ├── install.sh                     ← 初始化整個架構
    ├── install-agent.sh               ← 安裝指定 Agent + 建立 symlink
    ├── run-agent.sh                   ← 啟動 Agent（注入交接文件）
    └── hooks/
        ├── on-agent-stop.sh           ← 觸發：記憶整理 + git commit
        └── on-write.sh                ← 觸發：handoff 檔案自動 commit
```

---

## 3. Skill 系統設計

### 3.1 Skill 資料夾格式

每個 Skill 是一個**獨立資料夾**，內含標準化的 `SKILL.md`：

```
skill-name/
└── SKILL.md        ← YAML frontmatter + Markdown 內容
```

**SKILL.md 格式規範**：

```yaml
---
name: project-context          # 唯一識別名稱
description: 專案背景知識       # 簡短說明
version: 1.0
tags:
  - shared                     # shared = 共用技能
  - required                   # required = 所有 Agent 必載
scope: all                     # all / fetcher / fixer / developer
---

# （技能內容 Markdown）
```

### 3.2 技能繼承關係

```mermaid
graph TD
    subgraph 共用技能庫 .claude/skills/
        PC[project-context]
        GO[git-operations]
        BS[build-systems]
        CR[code-reading]
        HP[handoff-protocol]
    end

    subgraph featured/skills/
        F_PC[project-context] -.symlink.-> PC
        F_GO[git-operations]  -.symlink.-> GO
        F_HP[handoff-protocol]-.symlink.-> HP
        F_AD[agent-discovery 私有]
    end

    subgraph fetcher/skills/
        FT_PC[project-context]-.symlink.-> PC
        FT_GO[git-operations] -.symlink.-> GO
        FT_BS[build-systems]  -.symlink.-> BS
        FT_HP[handoff-protocol]-.symlink.->HP
        FT_BA[build-advanced 私有]
    end

    subgraph fixer/skills/
        FX_PC[project-context]-.symlink.-> PC
        FX_CR[code-reading]   -.symlink.-> CR
        FX_HP[handoff-protocol]-.symlink.->HP
        FX_EP[error-patterns 私有]
    end

    subgraph developer/skills/
        DV_PC[project-context]-.symlink.-> PC
        DV_CR[code-reading]   -.symlink.-> CR
        DV_HP[handoff-protocol]-.symlink.->HP
        DV_FP[feature-patterns 私有]
    end
```

### 3.3 按需載入機制

Claude Code 讀取 CLAUDE.md 時採**層級繼承**：

```
執行環境：agents/fetcher/
  ↓ Claude Code 讀取順序
  agents/fetcher/CLAUDE.md    ← 載入 fetcher 私有技能
        ↑ 自動繼承
  CLAUDE.md（根目錄）          ← @引用 .claude/skills/ 共用技能
```

**根目錄 `CLAUDE.md`（共用技能入口）**：

```markdown
# 全域背景

@.claude/skills/project-context/SKILL.md
@.claude/skills/git-operations/SKILL.md
@.claude/skills/handoff-protocol/SKILL.md
```

**`agents/fetcher/CLAUDE.md`（按需追加）**：

```markdown
# Fetcher 額外技能

@../../.claude/skills/build-systems/SKILL.md
@skills/build-advanced/SKILL.md
@../../memory/shared/project.md
```

---

## 4. 三區記憶架構

### 4.1 記憶區域定義

```
┌──────────────────────────────────────────────────────┐
│  ZONE 1：Shared Memory   memory/shared/               │
│  ┌────────────────────────────────────────────────┐  │
│  │  project.md     專案技術背景與架構               │  │
│  │  conventions.md 程式碼規範、命名慣例             │  │
│  │  decisions.md   跨 Agent 的重要決定              │  │
│  └────────────────────────────────────────────────┘  │
│  特性：所有 Agent 可讀寫 ｜ Git 追蹤 ｜ 永久保存    │
├──────────────────────────────────────────────────────┤
│  ZONE 2：Working Memory  memory/agents/{name}/        │
│  ┌────────────────────────────────────────────────┐  │
│  │  working.md     執行中的暫存思路與中間結果       │  │
│  └────────────────────────────────────────────────┘  │
│  特性：Agent 私有 ｜ 交接後清除 ｜ 可設定是否封存  │
├──────────────────────────────────────────────────────┤
│  ZONE 3：Handoff Memory  memory/handoffs/{run-id}/    │
│  ┌────────────────────────────────────────────────┐  │
│  │  01-fetcher.md  Claude 整理後的精華摘要（< 2K） │  │
│  │  02-fixer.md    下一個 Agent 的「收件匣」        │  │
│  └────────────────────────────────────────────────┘  │
│  特性：唯讀（寫後不修改） ｜ Git 追蹤 ｜ 可統計   │
└──────────────────────────────────────────────────────┘
```

### 4.2 記憶生命週期

```mermaid
stateDiagram-v2
    [*] --> WorkingEmpty : Agent 啟動

    WorkingEmpty --> WorkingActive : 注入 Handoff 文件\n+ 載入 Shared Memory

    WorkingActive --> WorkingActive : 執行任務\n（持續寫入 working.md）

    WorkingActive --> Summarizing : 任務完成\n觸發整理

    Summarizing --> HandoffWritten : Claude 壓縮摘要\n寫入 handoffs/{run}/

    HandoffWritten --> SharedUpdated : 有長期價值的知識\n寫回 shared/

    SharedUpdated --> WorkingCleared : 清除 working.md

    WorkingCleared --> GitCommitted : git commit\nhandoffs/ + shared/

    GitCommitted --> [*]
```

---

## 5. 工作流程設計

### 5.1 主流程

```mermaid
flowchart TD
    Start([使用者啟動]) --> FA[開啟 Featured Agent]

    FA --> Detect{偵測任務類型}

    Detect -->|需要下載/編譯| CheckFetcher{fetcher 已安裝?}
    Detect -->|已有 BUILD_FAILED| CheckFixer{fixer 已安裝?}
    Detect -->|已有 BUILD_SUCCESS| CheckDev{developer 已安裝?}

    CheckFetcher -->|否| PromptFetcher[輸出安裝提示\n並寫入交接文件]
    CheckFetcher -->|是| RunFetcher[啟動 Fetcher Agent]

    PromptFetcher --> UserInstall[使用者執行\ninstall-agent.sh fetcher]
    UserInstall --> RunFetcher

    RunFetcher --> BuildResult{編譯結果}

    BuildResult -->|BUILD_FAILED| CheckFixer
    BuildResult -->|BUILD_SUCCESS| CheckDev

    CheckFixer -->|否| PromptFixer[輸出安裝提示]
    CheckFixer -->|是| RunFixer[啟動 Fixer Agent]

    PromptFixer --> UserInstall2[使用者執行\ninstall-agent.sh fixer]
    UserInstall2 --> RunFixer

    RunFixer --> FixResult{修復結果}

    FixResult -->|FIX_SUCCESS| CheckDev
    FixResult -->|FIX_FAILED| ManualIntervention[提示人工介入]

    CheckDev -->|否| PromptDev[輸出安裝提示]
    CheckDev -->|是| RunDev[啟動 Developer Agent]

    PromptDev --> UserInstall3[使用者執行\ninstall-agent.sh developer]
    UserInstall3 --> RunDev

    RunDev --> Done([工作流程完成])

    ManualIntervention --> Done
```

### 5.2 交接時序圖

```mermaid
sequenceDiagram
    actor User
    participant Fetcher
    participant Memory as Memory System
    participant Git
    participant Hook as on-agent-stop.sh
    participant Fixer

    User->>Fetcher: run-agent.sh fetcher

    Note over Fetcher: 注入 working.md\n（來自 featured 交接）

    Fetcher->>Memory: 讀取 shared/project.md
    Fetcher->>Fetcher: 執行下載 + 編譯
    Fetcher->>Memory: 寫入 working.md（執行過程）

    Note over Fetcher: 任務結束，觸發交接程序

    Fetcher->>Memory: 整理 working.md → 摘要
    Fetcher->>Memory: 有價值知識 → shared/decisions.md
    Fetcher->>Memory: 寫入 handoffs/{run}/01-fetcher.md
    Fetcher->>Memory: 清除 working.md
    Fetcher-->>Hook: 輸出 HANDOFF_DONE:{...}

    Hook->>Git: git add memory/handoffs/ memory/shared/
    Hook->>Git: git commit "handoff: fetcher BUILD_FAILED"

    Hook-->>User: ⚠️ 需要安裝 fixer Agent\n執行: install-agent.sh fixer

    User->>User: install-agent.sh fixer

    User->>Fixer: run-agent.sh fixer

    Note over Fixer: 注入 working.md\n（來自 01-fetcher.md 摘要）

    Fixer->>Memory: 讀取 handoffs/{run}/01-fetcher.md
    Fixer->>Memory: 讀取 shared/（共用知識）
    Fixer->>Fixer: 分析錯誤 + 修復
```

---

## 6. 元件設計

### 6.1 registry.json

```json
{
  "schema_version": "1",
  "agents": {
    "featured": {
      "bundled": true,
      "description": "入口代理，任務偵測與安裝引導",
      "shared_skills": ["project-context", "git-operations", "handoff-protocol"],
      "private_skills": ["agent-discovery"]
    },
    "fetcher": {
      "bundled": false,
      "description": "下載專案並執行編譯",
      "install_cmd": "./scripts/install-agent.sh fetcher",
      "triggers": ["clone", "download", "build", "compile", "編譯"],
      "shared_skills": ["project-context", "git-operations", "build-systems", "handoff-protocol"],
      "private_skills": ["build-advanced"],
      "transitions": {
        "BUILD_SUCCESS": "developer",
        "BUILD_FAILED": "fixer"
      }
    },
    "fixer": {
      "bundled": false,
      "description": "分析並修復編譯錯誤",
      "install_cmd": "./scripts/install-agent.sh fixer",
      "triggers": ["BUILD_FAILED", "error", "fix", "修復"],
      "shared_skills": ["project-context", "code-reading", "handoff-protocol"],
      "private_skills": ["error-patterns"],
      "transitions": {
        "FIX_SUCCESS": "developer",
        "FIX_FAILED": null
      }
    },
    "developer": {
      "bundled": false,
      "description": "在成功編譯的專案上新增功能",
      "install_cmd": "./scripts/install-agent.sh developer",
      "triggers": ["BUILD_SUCCESS", "FIX_SUCCESS", "feature", "新增功能"],
      "shared_skills": ["project-context", "code-reading", "handoff-protocol"],
      "private_skills": ["feature-patterns"],
      "transitions": {}
    }
  }
}
```

### 6.2 agent-config.json

```json
{
  "_doc": "修改此檔案調整系統行為，所有值均有預設",

  "memory": {
    "shared_zone_enabled": true,
    "auto_summarize_before_handoff": true,
    "summarize_max_tokens": 2000,
    "clear_working_memory_after_handoff": true,
    "archive_before_clear": false,
    "archive_path": "memory/archive/"
  },

  "skills": {
    "shared_path": ".claude/skills",
    "on_demand": true,
    "always_load": ["project-context", "handoff-protocol"]
  },

  "handoff": {
    "agent_install_mode": "manual",
    "auto_git_commit": true,
    "git_remote": "origin",
    "git_branch": "main",
    "notify_user_on_missing_agent": true
  },

  "hooks": {
    "on_agent_stop": {
      "enabled": true,
      "summarize_memory": true,
      "git_commit_handoff": true
    },
    "on_write": {
      "enabled": true,
      "auto_commit_handoffs": true
    }
  }
}
```

### 6.3 交接文件格式（Handoff Document）

```markdown
---
schema: handoff-v1
run_id: "20240320-143022"
sequence: 1
from: fetcher
to: fixer
status: BUILD_FAILED
timestamp: "2024-03-20T14:30:22Z"
metrics:
  duration_seconds: 45
  tokens_estimated: 8500
memory_cleared: true
---

## 任務摘要
（3句話內）下載 my-project 並嘗試編譯，在 src/main.c:42
發現型別不匹配錯誤（int vs char*），編譯失敗。

## 關鍵發現
- 專案使用 GNU Make，進入點為 `make all`
- 錯誤位置：`src/main.c` 第 42 行
- 錯誤訊息：`incompatible pointer types passing 'char *' to parameter of type 'int'`
- 相關函式：`process_input(int flags)`

## 建議下一步
1. 將 `src/main.c:42` 的 `char *input` 改為 `int flags`
2. 重新執行 `make all` 驗證
3. 若有其他相依錯誤，繼續修復

## 上下文資料
- project_path: /tmp/my-project
- build_command: make all
- error_file: src/main.c
- shared_memory_updated: true
```

---

## 7. Hook 設計

### 7.1 Hook 事件對應

| 事件 | 觸發時機 | 對應 Script | 行為 |
|------|----------|-------------|------|
| `SubagentStop` | Agent 執行結束 | `on-agent-stop.sh` | 整理記憶、git commit、提示使用者 |
| `PostToolUse[Write]` | 寫入任何檔案 | `on-write.sh` | 若寫入 handoffs/ 則自動 git commit |
| `SessionStart` | Claude Code 啟動 | （預留）| 未來：自動注入交接文件 |

### 7.2 settings.json

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "matcher": ".*",
        "hooks": [{
          "type": "command",
          "command": "bash scripts/hooks/on-agent-stop.sh"
        }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [{
          "type": "command",
          "command": "bash scripts/hooks/on-write.sh"
        }]
      }
    ]
  },
  "permissions": {
    "allow": [
      "Bash(git:*)",
      "Bash(bash scripts/*)"
    ]
  }
}
```

---

## 8. 安裝腳本設計

### 8.1 install-agent.sh 流程

```mermaid
flowchart TD
    A[install-agent.sh AGENT_NAME] --> B{registry.json\n中存在?}
    B -->|否| ERR1[錯誤：列出可用 Agent]
    B -->|是| C[建立 agents/AGENT/skills/ 目錄]
    C --> D[讀取 registry.json\n取得 shared_skills 清單]
    D --> E{迴圈每個 shared_skill}
    E --> F{.claude/skills/SKILL\n資料夾存在?}
    F -->|否| WARN[警告：略過此技能]
    F -->|是| G{symlink 已存在?}
    G -->|是| SKIP[略過]
    G -->|否| H[ln -s 建立 symlink]
    H --> E
    SKIP --> E
    WARN --> E
    E -->|迴圈結束| I[驗證 SOUL.md 存在]
    I --> J{有待接交接文件?}
    J -->|是| K[提示: run-agent.sh AGENT_NAME]
    J -->|否| L[安裝完成]
    K --> L
```

### 8.2 run-agent.sh 流程

```mermaid
flowchart TD
    A[run-agent.sh AGENT_NAME] --> B{Agent 已安裝?}
    B -->|否| ERR[提示先執行 install-agent.sh]
    B -->|是| C[尋找最新交接文件\nmemory/handoffs/]
    C --> D{找到交接文件?}
    D -->|是| E[解析交接文件\n注入 memory/agents/AGENT/working.md]
    D -->|否| F[清空 working.md\n寫入「無前置交接」]
    E --> G[產生 run-id]
    F --> G
    G --> H[輸出啟動指引]
    H --> I[提示使用者在 Claude Code\n開啟 agents/AGENT/ 目錄]
```

---

## 9. 資料流設計

```mermaid
flowchart LR
    subgraph Input
        User([使用者])
        PrevHandoff[前一個交接文件]
    end

    subgraph Agent Execution
        WM[Working Memory\nworking.md]
        SM[Shared Memory\nshared/]
        Skills[Skill 讀取\n按需載入]
        Claude[Claude 執行]
    end

    subgraph Output
        NewHandoff[新交接文件\nhandoffs/run/]
        UpdatedShared[更新的 Shared\nshared/decisions.md]
        ClearedWM[清空的 Working\nworking.md]
    end

    subgraph Persistence
        Git[(Git Repository)]
    end

    User --> Claude
    PrevHandoff --> WM
    WM --> Claude
    SM --> Claude
    Skills --> Claude
    Claude --> WM
    Claude -->|整理摘要| NewHandoff
    Claude -->|長期知識| UpdatedShared
    Claude -->|清除| ClearedWM
    NewHandoff --> Git
    UpdatedShared --> Git
```

---

## 10. 未來遷移路徑

### 10.1 Claude Code → ADK/SDK 對應

| Claude Code 元件 | ADK/SDK 對應 |
|-----------------|-------------|
| `SOUL.md` + `DUTIES.md` | `AgentDefinition(description=..., prompt=...)` |
| `.claude/skills/` | `system_prompt` 中的知識注入 |
| `memory/handoffs/*.md` | 結構化 `output_format` JSON |
| Hooks（`on-agent-stop`） | `PostToolUse` callback |
| `run-agent.sh` | `query(prompt=..., options=ClaudeAgentOptions(resume=session_id))` |
| `agent-config.json` | `ClaudeAgentOptions` 參數 |

### 10.2 遷移時序

```mermaid
gantt
    title 遷移計畫
    dateFormat  YYYY-MM
    section Phase 1（現在）
    Claude Code 手動驗證    :active, p1, 2024-03, 2024-05
    交接文件格式確認        :p1b, 2024-03, 2024-04
    section Phase 2
    SDK 半自動化            :p2, 2024-05, 2024-07
    Handoff JSON 轉 output_format :p2b, 2024-05, 2024-06
    section Phase 3
    ADK 全自動化            :p3, 2024-07, 2024-09
    Featured Agent 自動安裝 :p3b, 2024-08, 2024-09
```

---

## 11. 設計決策紀錄（ADR）

| # | 決策 | 原因 | 取捨 |
|---|------|------|------|
| ADR-01 | Skill 以資料夾格式儲存（非單一檔案） | 未來可擴充（加 examples/、tests/ 等子檔案） | 略增目錄複雜度 |
| ADR-02 | Skill 共用以 symlink 實作 | 避免複製、單一事實來源 | Windows 不支援（本期限制） |
| ADR-03 | 工作記憶交接後清除 | 避免 Context 爆炸 | 需要完善摘要機制 |
| ADR-04 | 交接文件採 Markdown + YAML frontmatter | 人可讀、機器可解析、Git diff 友好 | 不如純 JSON 嚴格 |
| ADR-05 | run-id 採 timestamp | 簡單、不依賴外部服務 | 極低機率衝突 |
| ADR-06 | Agent 安裝預設手動 | 本期驗證安全性，未來再自動化 | 需使用者額外操作 |
