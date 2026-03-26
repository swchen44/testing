# Consys Experts — 設計書

**文件版本**：v3.0
**狀態**：Draft
**依據**：agents-requirements.md v3.0

> **注意**：本文件中所列的 expert、skill 名稱均為**示例**，用於說明命名規則與架構設計。實際 expert 與 skill 的規劃以團隊討論為準。

---

## 1. 系統架構總覽

### 1.1 Harness 架構觀

本系統依據 **Harness Engineering** 的精神設計（參考：[Birgitta Böckeler / Martin Fowler Blog](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html)）。

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Consys Expert Harness                        │
│                                                                     │
│  上下文工程  SKILL.md / expert.md / expert.local.md                 │
│  架構約束    Hooks（pre-compact）/ Hand-off 格式規範                 │
│  垃圾回收    session-end 整理記憶 / push connsys-memory              │
│                                                                     │
│         ↓ 透過以上三層強化 AI 核心能力（Think/Plan/Act/Learn）       │
│                                                                     │
│     Claude Code（現在）→ OpenClaw（Phase 2）→ ADK/SDK（Phase 3）    │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Script 實作語言優先策略

詳見 [§8 Script 實作語言優先策略](#8-script-實作語言優先策略)。

### 1.3 Consys Expert 組成

```
Consys Expert = Agent 核心能力 + Workflow（hooks）+ Tool（commands）+ Knowledge（skills）
              + Sub-Agent（agents）

每個 Expert 的內容分三個來源：
  ① framework-common-expert  → 跨所有 domain 共用
  ② {domain}-common-expert   → 該 domain 內部共用
  ③ {expert} private         → 該 Expert 自己的私有內容

全部透過 symlink 接入 workspace/.claude/（project level）
```

### 1.4 為什麼採用 Symlink 架構

**Agent 生態圈變化極快，設計必須有最大彈性。**

外部 Agent 框架（Claude Code、OpenClaw、ADK、gitagent 等）持續快速演進，採用 symlink 安裝模式的理由：

| 優點 | 說明 |
|------|------|
| **即換即生效** | 更改 expert 內容，下次 Claude 啟動即可看到，不需重裝 |
| **多版本共存** | 可以同時維護多個 Expert 版本，切換只需重新 link |
| **零侵入性** | Workspace 的 `.claude/` 只有 symlink，不污染 expert repo |
| **跨平台** | Linux/macOS 用 symlink；Windows 用 copy（自動降級） |
| **未來框架遷移** | 換成 OpenClaw 或其他框架時，install.py 只需改寫 target 路徑 |

參考：[open-gitagent/gitagent](https://github.com/open-gitagent/gitagent)

---

## 2. 五層資料夾設計（Layer 1–5）

### 2.1 層次總覽

```
connsys-experts/
│
├── {domain}/                              Layer 1：domain
│   ├── experts/                           Layer 2：internal experts
│   │   └── {domain}-{name}-expert/        Layer 3：expert（命名含 domain prefix）
│   │       ├── skills/                    Layer 4：工具資料夾
│   │       │   └── {domain}-{name}-{type}/  Layer 5：skill（命名含 domain + type）
│   │       │       └── SKILL.md
│   │       ├── hooks/
│   │       ├── commands/
│   │       │   └── {domain}-{name}-tool/
│   │       │       └── COMMAND.md
│   │       ├── agents/
│   │       │   └── {agent-name}.md
│   │       ├── test/
│   │       ├── report/
│   │       │   ├── execution-report.md    ← 人工維護
│   │       │   └── test-report.md     ← 人工維護
│   │       ├── expert.json
│   │       ├── expert.md
│   │       ├── soul.md
│   │       ├── rules.md
│   │       ├── duties.md
│   │       └── README.md
│   └── external-experts/                  Layer 2：external（照原名）
│       └── {original-tool-name}/          Layer 3：原始名稱
```

### 2.2 Layer 1：Domain 定義

| Domain | 用途 |
|--------|------|
| `framework` | 管理 Expert 用的 Expert（建立/強化 skill、memory、learn、反思回饋、找尋 expert） |
| `wifi` | Wi-Fi 相關開發 Expert（fw / driver / debug / CI/CD） |
| `bt` | Bluetooth 相關開發 Expert |
| `system` | System / Platform 相關開發 Expert |

### 2.3 Layer 2：Internal vs External

每個 domain 下固定有兩個子資料夾：

```
{domain}/
├── experts/            ← 內部 Expert（team 自行維護）
└── external-experts/   ← 外部工具（照原名，git submodule）
```

**External expert 的歸屬原則**：
- 討論後，各 domain 代表同意 → 放 `framework/external-experts/`（共用）
- 各 domain 自行維護 → 放各自的 `external-experts/`（命名不能衝突）

### 2.4 Layer 3：Expert 命名規則

**Internal expert**：
```
{domain}-{description}-expert

範例：
  framework-skill-create-expert
  framework-learn-expert
  wifi-common-expert          ← 每個 domain 必有的共用容器
  wifi-build-expert
  wifi-debug-expert
  wifi-cicd-expert
  bt-common-expert
  bt-build-expert
  system-common-expert
  system-device-expert
```

**`{domain}-common-expert` 的特殊規則**：
- 每個 domain 必有一個 `{domain}-common-expert`
- 作用：存放該 domain 內所有 expert 共用的 skill / hook / command
- `install.sh` 無作用（此 expert 僅作為容器，不直接安裝）
- `framework-common-expert` 特別：存放跨所有 domain 共用的 skill / hook

**External expert**：
```
照原始工具名稱（不加 domain prefix）

範例：
  skill-creator
  claude-memory-engine
  defuddle
```

### 2.5 Layer 4：Expert 內部資料夾

每個 expert 的資料夾結構（**expert 資料夾本身不含 install.sh 和 CLAUDE.md**，由頂層 `connsys-experts/install.py` 統一管理）：

```
{expert}/
│   # ── Core Identity (required) ────────────────────────────
├── expert.json    ← Manifest：name, version, owner, model, skills, tools,
│                     transitions, dependencies, exclude_symlink
├── soul.md        ← Identity, personality, communication style,
│                     Values & Principles, Collaboration Style
│
│   # ── Behavior & Rules ──────────────────────────────────
├── rules.md       ← must-always / must-never, Output Constraints,
│                     Interaction Boundaries
├── duties.md      ← Segregation of duties policy and role boundaries
├── expert.md      ← Key Behaviors, Constraints, Tools Available, Skills
│                     （install.py 讀此檔產生 CLAUDE.md @include）
│
│   # ── Content Folders ────────────────────────────────────
├── skills/        ← Knowledge：多個 skill 資料夾（每個 skill 見 Layer 5）
│   └── {domain}-{name}-{type}/
│       ├── SKILL.md
│       ├── README.md
│       ├── test/
│       └── report/
│
├── hooks/         ← Workflow：針對此 expert 的 hook（可選）
│   └── {hook-name}.sh     ← Shell 優先；複雜邏輯用 {hook-name}-helper.py
│
├── agents/        ← Sub-Agents：Claude subagent 定義（可選）
│   └── {agent-name}.md    ← subagent 的 prompt / 描述
│
├── commands/      ← Tool（相容層，Phase 1 不新增）
│   └── {domain}-{name}-tool/
│       └── COMMAND.md
│
├── test/          ← Expert 層級測試腳本
├── report/        ← 執行過程、結果（人工維護）
└── README.md      ← History、使用說明、設計說明
```

**`{domain}-common-expert` 的資料夾結構**（同上，作為共用資源容器）：

```
{domain}-common-expert/
├── expert.json    ← is_common: true, install_action: "none"
├── soul.md
├── rules.md
├── duties.md
├── expert.md
├── skills/        ← 此 domain 共用的 skills
├── hooks/         ← 此 domain 共用的 hooks（可選）
├── agents/        ← 此 domain 共用的 subagents（可選）
├── commands/      ← 此 domain 共用的 commands（可選）
├── test/
├── report/
└── README.md
```

> **agents/ 資料夾**：存放 Claude subagent 的 prompt 描述文件。subagent 是由主 Expert 呼叫的子任務 Agent，適合拆分為獨立工作單元（如：自動分析 log、自動查找 document）。參考：[open-gitagent/gitagent](https://github.com/open-gitagent/gitagent)

### 2.6 Layer 5：Skill 命名規則

**命名格式**：`[domain]-[skill-name]-[type]`

| 部分 | 說明 | 範例 |
|------|------|------|
| `[domain]` | Layer 1 的 domain 名稱 | `wifi`, `bt`, `framework` |
| `[skill-name]` | 描述性名稱（英文，用 `-` 分隔） | `build`, `coredump`, `handoff` |
| `[type]` | `flow` / `knowhow` / `tool` | `flow` |

**Type 定義**：

| Type | 用途 | 範例內容 |
|------|------|---------|
| `flow` | 有清楚步驟的工作流程 | 下載程式碼→編譯→解決 build error 的 SOP |
| `knowhow` | 基礎知識與背景資料 | Wi-Fi 協定知識、SW/HW 架構、程式碼規則、linker script rule、rom/ram patch rule、decode coredump、symbol map |
| `tool` | 外部工具的操作方法 | repo / gerrit 操作、preflight dashboard 查詢、tmux/ssh/uart/adb 控制裝置、AUTOTEST 操作、抓取 uart log、讀寫 Wiki / Gerrit / CR 系統 |

**Skill 命名範例**（以下為示例，非完整清單）：

```
# framework domain（跨 domain 共用）
framework-expert-discovery-knowhow   ← 有哪些 Expert 及各自能力
framework-handoff-flow               ← 交接流程 SOP
framework-memory-tool                ← connsys-memory 操作

# wifi domain
wifi-protocol-knowhow                ← Wi-Fi 協定基礎知識
wifi-arch-knowhow                    ← Wi-Fi SW/HW 架構
wifi-coderule-knowhow                ← 程式碼撰寫規則
wifi-build-flow                      ← fw 下載/編譯流程 SOP
wifi-drv-gen4m-build-flow            ← gen4m driver build 流程
wifi-builderror-knowhow              ← 特殊 compile error 處理
wifi-linkerscript-knowhow            ← Linker script 規則
wifi-rompatch-knowhow                ← ROM/RAM patch 規則
wifi-coredump-knowhow                ← Decode coredump 方法
wifi-symbolmap-knowhow               ← Symbol map 解讀
wifi-memory-knowhow                  ← 觀察 memory 使用
wifi-uart-tool                       ← 抓取 uart log
wifi-adbshell-tool                   ← adb shell 控制
wifi-autotest-tool                   ← AUTOTEST 平台操作
wifi-cicd-flow                       ← CI/CD 流程 SOP

# bt domain
bt-protocol-knowhow
bt-arch-knowhow
bt-coderule-knowhow                  ← bt 程式碼撰寫規則
bt-build-flow
bt-fw-build-flow                     ← bt fw 完整 build 流程

# system domain（跨 wifi/bt/system 共用工具）
system-gerrit-tool                   ← Gerrit 操作（原 wifi-gerrit-tool）
system-repo-multi-repo-tool          ← Android repo / multi-repo 操作（原 wifi-repo-tool）
system-preflight-tool                ← Preflight dashboard 查詢（原 wifi-preflight-tool）
system-core-tracer-gdb-tool          ← CoreTracer / GDB 工具操作
system-device-tool                   ← 裝置控制（tmux/ssh/uart/adb）
system-cicd-tool
```

### 2.7 Layer 5：Skill 內部資料夾

每個 Skill 資料夾（`{domain}-{name}-{type}/`）的標準結構：

```
{domain}-{name}-{type}/          Layer 5：skill 資料夾
├── SKILL.md                     ← Skill 主體（YAML frontmatter + 內容）
├── README.md                    ← History、使用說明、人工安裝說明、Design、目的、開發說明
├── test/                        ← Skill 測試腳本（Shell 優先）
│   ├── test-basic.sh            ← Shell：基本功能驗證（必要）
│   ├── test_{skill_name}.py     ← Python pytest：unit test（有複雜邏輯時加）
│   ├── conftest.py              ← pytest fixtures（可選）
│   └── test-data.json           ← 測試輸入資料（可選）
└── report/                      ← 執行過程、結果、token 用量
    ├── execution-report.md      ← 人工維護
    └── test-report.md           ← 人工或 CI 自動生成
```

| 檔案/資料夾 | 用途 | 維護方式 |
|-----------|------|---------|
| `SKILL.md` | Skill 主體，Claude 在執行時讀取 | 人工撰寫，`framework-learn-expert` 未來可自動更新 |
| `README.md` | History、使用說明、人工安裝說明、Design、目的；**開發說明也寫在這裡** | 人工維護 |
| `test/test-basic.sh` | Shell 驗證 skill 主要功能，所有 skill 必備 | 人工撰寫，CI 可自動執行 |
| `test/test_xxx.py` | pytest unit test，適用有 Python helper 的 skill | 人工撰寫，`pytest test/` 自動執行 |
| `report/` | 每次執行的過程記錄、結果摘要、token 用量統計 | 人工或 hook 自動寫入 |

**Command 命名規則**（同 Skill，type 固定為 `tool`）：
```
{domain}-{name}-tool/
  └── COMMAND.md

範例：
  framework-experts-tool/    ← /experts 指令
  framework-handoff-tool/    ← /handoff 指令
```

---

## 3. 完整目錄結構

```
connsys-experts/ (git)
├── README.md
├── registry.json                            ← 全域 Expert 目錄
├── install.sh                               ← 頂層：env vars + clone connsys-memory
│
├── framework/
│   ├── experts/
│   │   ├── framework-common-expert/         ← 跨所有 domain 共用（install.sh 無作用）
│   │   │   ├── README.md
│   │   │   ├── install.sh                   ← 無作用
│   │   │   ├── expert.json
│   │   │   ├── skills/
│   │   │   │   ├── framework-expert-discovery-knowhow/  ← Layer 5 完整示例
│   │   │   │   │   ├── SKILL.md             ← Skill 主體
│   │   │   │   │   ├── README.md            ← History、使用說明、Design、目的
│   │   │   │   │   ├── test/               ← Skill 測試腳本或測試用 JSON
│   │   │   │   │   └── report/             ← 執行過程、結果、token 用量
│   │   │   │   ├── framework-handoff-flow/ ← 以下 skill 均同 Layer 5 結構（SKILL.md / README.md / test/ / report/）
│   │   │   │   │   └── SKILL.md
│   │   │   │   └── framework-memory-tool/
│   │   │   │       └── SKILL.md
│   │   │   ├── hooks/                       ← 所有 Expert 共用的 hooks（Shell 優先）
│   │   │   │   ├── session-start.sh         ← 載入交接文件與共用記憶
│   │   │   │   ├── session-end.sh           ← 儲存記憶、push connsys-memory
│   │   │   │   ├── pre-compact.sh           ← context 壓縮前存快照
│   │   │   │   ├── mid-session-checkpoint.sh← 每 20 訊息存檔
│   │   │   │   ├── shared-utils.sh          ← 共用 Shell functions
│   │   │   │   └── memory-helper.py         ← 複雜記憶操作（JSON/YAML 解析等）
│   │   │   ├── commands/
│   │   │   │   ├── framework-experts-tool/
│   │   │   │   │   └── COMMAND.md
│   │   │   │   └── framework-handoff-tool/
│   │   │   │       └── COMMAND.md
│   │   │   ├── test/                        ← Expert 層級測試腳本
│   │   │   └── report/                      ← 執行過程、結果、token 用量
│   │   │
│   │   ├── framework-skill-create-expert/
│   │   │   ├── README.md
│   │   │   ├── install.sh
│   │   │   ├── expert.json
│   │   │   ├── CLAUDE.md
│   │   │   ├── skills/
│   │   │   │   ├── framework-skill-create-flow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   └── framework-skill-evaluate-knowhow/
│   │   │   │       └── SKILL.md
│   │   │   ├── hooks/
│   │   │   ├── commands/
│   │   │   ├── test/
│   │   │   └── report/
│   │   │
│   │   └── framework-learn-expert/
│   │       ├── README.md
│   │       ├── install.sh
│   │       ├── expert.json
│   │       ├── CLAUDE.md
│   │       ├── skills/
│   │       │   ├── framework-learn-flow/
│   │       │   │   └── SKILL.md
│   │       │   └── framework-feedback-knowhow/
│   │       │       └── SKILL.md
│   │       ├── hooks/
│   │       ├── commands/
│   │       ├── test/
│   │       └── report/
│   │
│   └── external-experts/
│       ├── skill-creator/                   ← git submodule
│       └── claude-memory-engine/            ← git submodule（參考實作）
│
├── wifi/
│   ├── experts/
│   │   ├── wifi-common-expert/              ← wifi domain 共用（install.sh 無作用）【示例】
│   │   │   ├── README.md
│   │   │   ├── install.sh                   ← 無作用
│   │   │   ├── expert.json
│   │   │   ├── skills/
│   │   │   │   ├── wifi-protocol-knowhow/   ← Wi-Fi 協定基礎知識
│   │   │   │   │   └── SKILL.md
│   │   │   │   ├── wifi-arch-knowhow/       ← SW/HW 架構知識
│   │   │   │   │   └── SKILL.md
│   │   │   │   └── wifi-coderule-knowhow/   ← 程式碼撰寫規則
│   │   │   │       └── SKILL.md
│   │   │   │   # 注：gerrit/repo/preflight 工具移至 system domain
│   │   │   ├── hooks/                       ← wifi 專屬 hooks（可選）
│   │   │   ├── commands/
│   │   │   ├── test/
│   │   │   └── report/
│   │   │
│   │   ├── wifi-build-expert/               ← 【示例】
│   │   │   ├── README.md
│   │   │   ├── install.sh                   ← 依 expert.json 安裝三層 symlinks
│   │   │   ├── expert.json
│   │   │   ├── CLAUDE.md
│   │   │   ├── skills/
│   │   │   │   ├── wifi-build-flow/         ← fw build 流程 SOP
│   │   │   │   │   └── SKILL.md
│   │   │   │   ├── wifi-drv-gen4m-build-flow/ ← gen4m driver build 流程
│   │   │   │   │   └── SKILL.md
│   │   │   │   ├── wifi-builderror-knowhow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   ├── wifi-linkerscript-knowhow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   └── wifi-rompatch-knowhow/
│   │   │   │       └── SKILL.md
│   │   │   ├── hooks/
│   │   │   ├── commands/
│   │   │   ├── test/
│   │   │   └── report/
│   │   │
│   │   ├── wifi-debug-expert/
│   │   │   ├── README.md
│   │   │   ├── install.sh
│   │   │   ├── expert.json
│   │   │   ├── CLAUDE.md
│   │   │   ├── skills/
│   │   │   │   ├── wifi-debug-flow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   ├── wifi-coredump-knowhow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   ├── wifi-symbolmap-knowhow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   ├── wifi-memory-knowhow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   ├── wifi-uart-tool/
│   │   │   │   │   └── SKILL.md
│   │   │   │   └── wifi-adbshell-tool/
│   │   │   │       └── SKILL.md
│   │   │   ├── hooks/
│   │   │   ├── commands/
│   │   │   ├── test/
│   │   │   └── report/
│   │   │
│   │   └── wifi-cicd-expert/                ← 【示例】
│   │       ├── README.md
│   │       ├── install.sh
│   │       ├── expert.json
│   │       ├── CLAUDE.md
│   │       ├── skills/
│   │       │   ├── wifi-cicd-flow/
│   │       │   │   └── SKILL.md
│   │       │   └── wifi-autotest-tool/      ← AUTOTEST 平台操作
│   │       │       └── SKILL.md
│   │       │   # 注：preflight 工具移至 system domain
│   │       ├── hooks/
│   │       ├── commands/
│   │       ├── test/
│   │       └── report/
│   │
│   └── external-experts/                    ← wifi 特定的外部工具
│
├── bt/
│   ├── experts/
│   │   ├── bt-common-expert/                ← bt domain 共用【示例】
│   │   │   ├── README.md
│   │   │   ├── install.sh                   ← 無作用
│   │   │   ├── expert.json
│   │   │   ├── skills/
│   │   │   │   ├── bt-protocol-knowhow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   ├── bt-arch-knowhow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   └── bt-coderule-knowhow/     ← bt 程式碼撰寫規則
│   │   │   │       └── SKILL.md
│   │   │   │   # 注：bt-coredump-knowhow / bt-gerrit-tool 已移除
│   │   │   │   # 注：gerrit 工具改由 system-gerrit-tool 提供
│   │   │   ├── hooks/
│   │   │   ├── commands/
│   │   │   ├── test/
│   │   │   └── report/
│   │   ├── bt-build-expert/                 ← 【示例】
│   │   │   ├── skills/
│   │   │   │   ├── bt-build-flow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   └── bt-fw-build-flow/        ← bt fw 完整 build 流程
│   │   │   │       └── SKILL.md
│   │   │   ├── hooks/ ├── commands/ ├── test/ └── report/
│   │   └── bt-debug-expert/                 ← 【示例】
│   │       ├── skills/ ├── hooks/ ├── commands/ ├── test/ └── report/
│   └── external-experts/
│
└── system/
    ├── experts/
    │   ├── system-common-expert/            ← system domain 共用（含跨 domain 工具）【示例】
    │   │   ├── README.md
    │   │   ├── install.sh                   ← 無作用
    │   │   ├── expert.json
    │   │   ├── skills/
    │   │   │   ├── system-gerrit-tool/      ← Gerrit 操作（原 wifi-gerrit-tool）
    │   │   │   │   └── SKILL.md
    │   │   │   ├── system-repo-multi-repo-tool/ ← Android repo / multi-repo 操作（原 wifi-repo-tool）
    │   │   │   │   └── SKILL.md
    │   │   │   ├── system-preflight-tool/   ← Preflight dashboard 查詢（原 wifi-preflight-tool）
    │   │   │   │   └── SKILL.md
    │   │   │   ├── system-core-tracer-gdb-tool/ ← CoreTracer / GDB 工具操作
    │   │   │   │   └── SKILL.md
    │   │   │   └── system-device-tool/      ← tmux/ssh/uart/adb 裝置控制
    │   │   │       └── SKILL.md
    │   │   ├── hooks/ ├── commands/ ├── test/ └── report/
    │   ├── system-cicd-expert/              ← 【示例】
    │   │   ├── skills/ ├── hooks/ ├── commands/ ├── test/ └── report/
    │   └── system-device-expert/            ← 【示例】
    │       ├── skills/ ├── hooks/ ├── commands/ ├── test/ └── report/
    └── external-experts/
```

---

## 4. `expert.json` 格式

### 4.1 一般 Expert（有 dependencies）

```json
{
  "name": "wifi-build-expert",
  "display_name": "WiFi Build Expert",
  "domain": "wifi",
  "owner": "wifi-team",
  "description": "專門處理 Wi-Fi 韌體下載、編譯與 build error 排查",
  "version": "1.0.0",
  "triggers": ["build", "compile", "編譯", "BUILD_FAILED"],
  "transitions": {
    "BUILD_SUCCESS": "wifi-cicd-expert",
    "BUILD_FAILED": null
  },
  "dependencies": {
    "framework-common-expert": {
      "skills": [
        "framework-expert-discovery-knowhow",
        "framework-handoff-flow",
        "framework-memory-tool"
      ],
      "hooks": [
        "session-start",
        "session-end",
        "pre-compact",
        "mid-session-checkpoint"
      ],
      "commands": [
        "framework-experts-tool",
        "framework-handoff-tool"
      ]
    },
    "wifi-common-expert": {
      "skills": [
        "wifi-protocol-knowhow",
        "wifi-arch-knowhow",
        "wifi-coderule-knowhow"
      ],
      "hooks": [],
      "commands": []
    },
    "system-common-expert": {
      "skills": [
        "system-gerrit-tool",
        "system-repo-multi-repo-tool"
      ],
      "hooks": [],
      "commands": []
    }
  },
  "private": {
    "skills": [
      "wifi-build-flow",
      "wifi-builderror-knowhow",
      "wifi-linkerscript-knowhow",
      "wifi-rompatch-knowhow"
    ],
    "hooks": [],
    "commands": []
  },
  "scenarios": ["agent-first", "legacy"],
  "human_in_the_loop": {
    "require_confirm": ["git push", "make clean"]
  }
}
```

### 4.2 Common Expert（無 dependencies，僅描述）

```json
{
  "name": "wifi-common-expert",
  "display_name": "WiFi Common (shared container)",
  "domain": "wifi",
  "description": "wifi domain 共用 skill/hook/command 的容器",
  "version": "1.0.0",
  "is_common": true,
  "install_action": "none",
  "exclude_symlink": {
    "skills": [],
    "hooks":  [],
    "agents": []
  }
}
```

---

## 5. install.py 設計

`install.py` 是 **connsys-experts 根目錄唯一的安裝程式**，以 Python stdlib 實作，用 `uv run` 執行。Expert 資料夾**不再含 install.sh**。

### 5.1 執行方式與參數

```bash
# 安裝指令（所有指令後都需 source .env）
uv run ./connsys-experts/install.py --init   framework/experts/framework-common-expert/expert.json
uv run ./connsys-experts/install.py --add    wifi/experts/wifi-build-expert/expert.json
uv run ./connsys-experts/install.py --remove wifi/experts/wifi-build-expert/expert.json
uv run ./connsys-experts/install.py --uninstall

# 查詢 / 診斷
uv run ./connsys-experts/install.py --list
uv run ./connsys-experts/install.py --doctor

# source 環境變數（每次執行 install.py 後都需要）
source .connsys-expert/.env
```

| 指令 | 說明 | 影響範圍 |
|------|------|---------|
| `--init <expert.json>` | **全新安裝**：清除所有既有 link，重建 CLAUDE.md，建立 symlink | 全部重建 |
| `--add <expert.json>` | **疊加安裝**：保留既有 link，加入此 Expert 的 link，更新 CLAUDE.md | 新增 |
| `--remove <expert.json>` | **移除**：移除此 Expert 的 link，重建 CLAUDE.md（若有其他 Expert 仍保留） | 重建 link |
| `--uninstall` | **完全清除**：移除所有 link 和 CLAUDE.md，保留 `.connsys-expert/` 的 log/memory | 清 link |
| `--list` | 列出目前 `.claude/` 中所有已安裝的 symlink 及來源 Expert | 唯讀 |
| `--doctor` | 診斷 symlink 健康、環境版本（Python/uv/uvx）| 唯讀 |

> 每次 `--init`、`--add`、`--remove` 後，install.py 自動印出提示：
> ```
> ✅ 安裝完成。請執行：source .connsys-expert/.env
> ```

### 5.2 install.py 的 Symlink 建立邏輯

install.sh 讀取 `expert.json` 的 `dependencies` + `private`，依序在 workspace `.claude/` 建立 symlinks：

```
安裝 wifi-build-expert 時的 .claude/ 結果：

.claude/
├── skills/
│   ├── framework-expert-discovery-knowhow  → $CONNSYS_EXPERTS_PATH/framework/experts/framework-common-expert/skills/framework-expert-discovery-knowhow/
│   ├── framework-handoff-flow              → $CONNSYS_EXPERTS_PATH/framework/experts/framework-common-expert/skills/framework-handoff-flow/
│   ├── framework-memory-tool               → $CONNSYS_EXPERTS_PATH/framework/experts/framework-common-expert/skills/framework-memory-tool/
│   ├── wifi-protocol-knowhow               → $CONNSYS_EXPERTS_PATH/wifi/experts/wifi-common-expert/skills/wifi-protocol-knowhow/
│   ├── wifi-arch-knowhow                   → $CONNSYS_EXPERTS_PATH/wifi/experts/wifi-common-expert/skills/wifi-arch-knowhow/
│   ├── wifi-coderule-knowhow               → $CONNSYS_EXPERTS_PATH/wifi/experts/wifi-common-expert/skills/wifi-coderule-knowhow/
│   ├── system-gerrit-tool                  → $CONNSYS_EXPERTS_PATH/system/experts/system-common-expert/skills/system-gerrit-tool/
│   ├── system-repo-multi-repo-tool         → $CONNSYS_EXPERTS_PATH/system/experts/system-common-expert/skills/system-repo-multi-repo-tool/
│   ├── wifi-build-flow                     → $CONNSYS_EXPERTS_PATH/wifi/experts/wifi-build-expert/skills/wifi-build-flow/
│   └── wifi-builderror-knowhow             → $CONNSYS_EXPERTS_PATH/wifi/experts/wifi-build-expert/skills/wifi-builderror-knowhow/
│
├── hooks/                                  ← 來自 framework-common-expert（Shell 優先）
│   ├── session-start.sh          → $CONNSYS_EXPERTS_PATH/framework/experts/framework-common-expert/hooks/session-start.sh
│   ├── session-end.sh            → .../framework-common-expert/hooks/session-end.sh
│   ├── pre-compact.sh            → .../framework-common-expert/hooks/pre-compact.sh
│   ├── mid-session-checkpoint.sh → .../framework-common-expert/hooks/mid-session-checkpoint.sh
│   ├── shared-utils.sh           → .../framework-common-expert/hooks/shared-utils.sh
│   └── memory-helper.py          → .../framework-common-expert/hooks/memory-helper.py
│
├── commands/
│   ├── framework-experts-tool    → .../framework-common-expert/commands/framework-experts-tool/
│   └── framework-handoff-tool    → .../framework-common-expert/commands/framework-handoff-tool/
│
└── memory/                                 ← 本地三區記憶（install.sh 首次執行時建立）
    ├── shared/                             ← Zone 1：跨 Expert 持久共用知識
    │   ├── project.md
    │   ├── conventions.md
    │   └── decisions.md
    ├── working/                            ← Zone 2：當前 Expert 飛行中狀態（切換時清除）
    │   └── wifi-build-expert/
    │       └── working.md
    └── handoffs/                           ← Zone 3：交接文件（寫入後唯讀）
        └── {run-id}/
            └── handoff.md
```

### 5.3 .connsys-expert/ 隱藏資料夾設計

install.py 在 workspace 根目錄建立隱藏資料夾 `.connsys-expert/`，存放所有 runtime 資料：

```
workspace/
├── .connsys-expert/              ← install.py 建立（.gitignore 排除）
│   ├── .env                      ← 環境變數（source .connsys-expert/.env）
│   ├── .installed-experts        ← 目前已安裝的 Expert 清單（每行一個 expert.json path）
│   ├── log/                      ← install.py 執行 debug log
│   │   └── 2026-03-26/
│   │       └── install.log
│   └── memory/                   ← 本地記憶（session-stop 時上傳 connsys-memory repo）
│       └── {expert-name}/
│           └── 2026-03-26/
│               └── 10:30-wifi-build-expert-memory.md
└── CLAUDE.md                     ← install.py 生成（@include expert.md 等）
```

> Windows 不支援 symlink 時，install.py 自動降級為 copy 模式（功能相同，但更新 expert 後需重新安裝）。

### 5.4 .env 環境變數設計

install.py 執行後，將環境變數寫入 `.connsys-expert/.env`：

```bash
# .connsys-expert/.env（由 install.py 生成，勿手動編輯）
export CONNSYS_EXPERTS_PATH="/Users/john.doe/workspace/connsys-experts"
export CONNSYS_EXPERTS_WORKSPACE_ROOT_PATH="/Users/john.doe/workspace"
export CONNSYS_EXPERTS_CODE_SPACE_PATH="/Users/john.doe/workspace/codespace"
export CONNSYS_EXPERTS_MEMORY_PATH="/Users/john.doe/workspace/.connsys-expert/memory"
export CONNSYS_EXPERTS_EMPLOYEE_ID="john.doe"
export CONNSYS_EXPERTS_ACTIVE_EXPERT="wifi-build-expert"
```

使用者每次執行 install.py 後需手動 source：
```bash
source .connsys-expert/.env
```

> install.py 執行結束後自動印出提示，避免忘記 source。

### 5.5 多 Expert 安裝設計（--init / --add）

**設計原則**：`--init` 是全新安裝（清除重建）；`--add` 是疊加安裝（保留既有，加入新的）。每次安裝完成後，`.claude/` 中的所有 link 皆對應到目前已安裝的 Expert 集合。

**依賴解析流程**：

```
install.py --add wifi/experts/wifi-build-expert/expert.json

Step 1：讀取 expert.json，取得 dependencies 清單
  dependencies: ["framework/experts/framework-common-expert", "wifi/experts/wifi-common-expert"]

Step 2：遞迴讀取所有依賴的 expert.json，合併所有要建立的 link
  framework-common-expert → skills/*、hooks/*、agents/*
  wifi-common-expert      → skills/*
  wifi-build-expert       → skills/*（private）

Step 3：套用 exclude_symlink 過濾不需要的 link
  wifi-build-expert.json 中若設定 "skills": ["wifi-linkerscript-knowhow"]
  則不建立該 skill 的 link

Step 4：清除舊 link，重建 .claude/skills/、hooks/、agents/、commands/

Step 5：更新 .connsys-expert/.installed-experts
Step 6：重新生成 workspace/CLAUDE.md（詳見 §9）
Step 7：更新 .connsys-expert/.env
Step 8：印出變更清單（新增/移除/保留）+ source 提示
```

**推薦安裝流程**：

```bash
# 全新安裝（第一次）
uv run ./connsys-experts/install.py --init framework/experts/framework-common-expert/expert.json
source .connsys-expert/.env

# 加入 wifi-build-expert（自動帶入 dependencies）
uv run ./connsys-experts/install.py --add wifi/experts/wifi-build-expert/expert.json
source .connsys-expert/.env

# 查看安裝結果
uv run ./connsys-experts/install.py --list
```

### 5.6 --doctor 診斷輸出

```
$ uv run ./connsys-experts/install.py --doctor

=== Connsys Experts Doctor ===

已安裝的 Experts：
  [1] framework-common-expert  (framework/experts/framework-common-expert)
  [2] wifi-build-expert        (wifi/experts/wifi-build-expert)

Symlinks 健康狀態：
  Skills：
    ✅ framework-expert-discovery-knowhow  → .../framework-common-expert/skills/...  OK
    ✅ wifi-build-flow                     → .../wifi-build-expert/skills/...        OK
    ❌ wifi-linkerscript-knowhow           → .../wifi-build-expert/skills/...        DANGLING
  Hooks：
    ✅ session-start.sh  → .../framework-common-expert/hooks/session-start.sh  OK
    ✅ session-end.sh    → .../framework-common-expert/hooks/session-end.sh    OK
  Agents：
    ✅ log-analyzer.md   → .../framework-common-expert/agents/log-analyzer.md  OK

環境檢查：
  Python (system): 3.11.8  ✅ (>= 3.11)
  uv:              0.4.2   ✅ 已安裝
  uvx:             0.4.2   ✅ 已安裝

建議修復：
  → 刪除 dangling link: .claude/skills/wifi-linkerscript-knowhow
    python3 -c "import os; os.remove('.claude/skills/wifi-linkerscript-knowhow')"
```

---

## 6. 環境變數設計

install.py 執行後將環境變數寫入 `workspace/.connsys-expert/.env`，使用者手動 source 後即可在 skill、hook、agent 中使用。
所有變數統一使用 `CONNSYS_EXPERTS_` 前綴：

```bash
export CONNSYS_EXPERTS_PATH="..."                              # connsys-experts repo 路徑
export CONNSYS_EXPERTS_WORKSPACE_ROOT_PATH="$(pwd)"           # workspace 根目錄（.claude/ 所在）
export CONNSYS_EXPERTS_CODE_SPACE_PATH="..."                  # 程式碼路徑（agent-first: codespace/；legacy: workspace root）
export CONNSYS_EXPERTS_MEMORY_PATH="$(pwd)/connsys-memory"     # connsys-memory repo 路徑
export CONNSYS_EXPERTS_EMPLOYEE_ID="$(git config user.name)"  # 員工工號
```

| 變數 | Agent First | Legacy |
|------|-------------|--------|
| `CONNSYS_EXPERTS_WORKSPACE_ROOT_PATH` | `~/workspace` | `~/workspace` |
| `CONNSYS_EXPERTS_CODE_SPACE_PATH` | `~/workspace/codespace` | `~/workspace` |

---

## 7. SKILL.md 格式

```yaml
---
name: wifi-build-flow
description: "Wi-Fi 韌體下載與編譯流程 SOP，包含 Android repo tool 操作與 build error 處理"
version: "1.0.0"
domain: wifi
type: flow
scope: wifi-build-expert
tags: [internal, private]
---

# WiFi Build Flow

## 步驟 1：下載程式碼
使用 Android repo tool：
```bash
cd $CONNSYS_EXPERTS_CODE_SPACE_PATH
mkdir fw && cd fw
repo init -u {manifest-url} -m {manifest.xml}
repo sync -j8
```

## 步驟 2：編譯
...

## 步驟 3：解決 Build Error
參考 wifi-builderror-knowhow skill。
```

**Type 欄位值**：`flow` / `knowhow` / `tool`

---

## 8. Script 實作語言優先策略

適用範圍：所有 Hook（`hooks/`）與 Skill 內的可執行腳本（`test/`、helper scripts）。

### 8.1 語言優先順序

```
優先順序：Shell（預設）→ Python（複雜邏輯）→ JS（OpenClaw 遷移備用）

判斷原則：
  ① 能用 Shell 解決的，就用 Shell
     - 適合：git 操作、檔案讀寫、環境變數、簡單字串處理、基本功能驗證
     - 優點：所有開發環境普遍存在，無需額外 runtime，韌體工程師熟悉

  ② Shell 難以維護時，改用 Python
     - 適合：JSON/YAML 解析、複雜字串處理、API 呼叫、跨平台邏輯、unit test
     - 優點：韌體團隊的第二語言，函式庫豐富（GitPython、requests、pyyaml）
     - 慣例：Shell hook 以 subprocess 呼叫 Python helper（同名 .py 檔）

  ③ JS 為最後考慮，保留作為 OpenClaw 遷移路徑
     - 適合：Phase 2 OpenClaw 遷移時，TypeScript 重寫的過渡期
     - 原則：Phase 1 不主動新增 JS hooks
```

### 8.2 檔案命名慣例

| 情況 | 命名 | 範例 |
|------|------|------|
| 純 Shell hook | `{name}.sh` | `session-start.sh` |
| Shell + Python helper | `{name}.sh` + `{name}-helper.py` | `session-end.sh` + `session-end-helper.py` |
| 複雜邏輯獨立為 Python | `{name}.py`（由 Shell wrapper 呼叫）| `compress-memory.py` |
| Skill 基本測試 | `test-basic.sh` | Shell 驗證 skill 主要功能 |
| Skill pytest | `test_{name}.py` | Python unit test，放 `test/` 下 |

### 8.3 Python 規範：PEP 723

所有 Hook helper 與 Skill 內的 Python 腳本，**強制採用 PEP 723 Inline Script Metadata**。

> **stdlib 優先原則**：儘量使用 Python 標準內建 library（`os`、`pathlib`、`json`、`subprocess` 等），減少 `dependencies` 欄位的外部套件，讓使用者可直接 `uv run` 一鍵執行，無需等待大量套件安裝。

參考：[PEP 723 — Inline script metadata](https://peps.python.org/pep-0723/)

#### 標準模板

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "requests>=2.31",
# ]
# ///

import sys
# 依賴在頂端 metadata 宣告後正常 import

def main() -> None:
    pass

if __name__ == "__main__":
    main()
```

| 好處 | 說明 |
|------|------|
| **零 venv 管理** | 不需 `requirements.txt`、不需建 venv，依賴宣告在腳本本身 |
| **直接執行** | `uv run script.py` 自動安裝依賴並執行 |
| **自帶文件** | 查看腳本即知依賴版本，降低環境不一致問題 |
| **CI 友善** | CI 環境只需安裝 `uv`，不需管理每個 skill 的 venv |

#### 執行方式

| 方式 | 指令 | 說明 |
|------|------|------|
| **推薦：uv run** | `uv run script.py` | 自動讀取 inline metadata，安裝依賴後執行 |
| 已有環境 | `python3 script.py` | 依賴已安裝時可直接執行 |
| pytest | `pytest test/` | 執行 `test/` 下所有 `test_*.py` |

> 安裝 `uv`：`curl -LsSf https://astral.sh/uv/install.sh | sh`

### 8.4 Skill pytest 範例（test_xxx.py）

```python
# test/test_wifi_build_flow.py
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pytest>=8.0",
# ]
# ///
"""wifi-build-flow skill 的 unit test"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def test_data():
    data_file = Path(__file__).parent / "test-data.json"
    return json.loads(data_file.read_text())


def test_build_command_format(test_data):
    """驗證 build 指令格式正確"""
    cmd = test_data["build_cmd"]
    assert "make" in cmd
    assert "-j" in cmd


def test_output_dir_path():
    """驗證 build 輸出目錄路徑格式"""
    path = f"$CONNSYS_EXPERTS_CODE_SPACE_PATH/fw/bora/build/out"
    assert "build/out" in path
```

### 8.5 Hook Python Helper 範例（含 PEP 723）

更新後的 `memory-helper.py`（由 `session-end.sh` 呼叫）：

```python
# memory-helper.py
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""connsys-memory 複雜操作 helper
由 Shell hooks 呼叫，處理 YAML frontmatter 解析、token 計算等 Shell 難以完成的邏輯。
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime, timezone


def mark_handoff_read(handoff_path: str) -> None:
    """在 handoff frontmatter 中標記 read_at timestamp"""
    if not handoff_path:
        return
    path = Path(handoff_path)
    if not path.exists():
        return
    content = path.read_text()
    if content.startswith("---"):
        end = content.find("---", 3)
        fm = yaml.safe_load(content[3:end])
        fm["read_at"] = datetime.now(timezone.utc).isoformat()
        new_fm = yaml.dump(fm, allow_unicode=True)
        path.write_text(f"---\n{new_fm}---{content[end+3:]}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "mark-handoff-read":
        mark_handoff_read(sys.argv[2] if len(sys.argv) > 2 else "")
```

---

## 9. CLAUDE.md 生成機制

install.py 在 `$CONNSYS_EXPERTS_WORKSPACE_ROOT_PATH`（workspace 根目錄）生成 `CLAUDE.md`。

### 9.1 單 Expert 安裝

```markdown
# Consys Expert: WiFi Build Expert

@connsys-experts/wifi/experts/wifi-build-expert/expert.md
@connsys-experts/wifi/experts/wifi-build-expert/soul.md
@connsys-experts/wifi/experts/wifi-build-expert/rules.md
@connsys-experts/wifi/experts/wifi-build-expert/duties.md
@CLAUDE.local.md
```

> `@include` 直接指向 expert 資料夾內的檔案（symlink 到 `connsys-experts/`），更新 expert 後不需重新安裝即可生效。

### 9.2 多 Expert 安裝（--add 疊加）

安裝多個 Expert 時，CLAUDE.md 以**最後安裝的 Expert** 的 identity 檔為主（soul、rules、duties），加入所有已安裝 Expert 的 expert.md：

```markdown
# Consys Experts（2 Experts 已安裝）

## Expert Identity（以最後安裝的 Expert 為主）
@connsys-experts/wifi/experts/wifi-build-expert/soul.md
@connsys-experts/wifi/experts/wifi-build-expert/rules.md
@connsys-experts/wifi/experts/wifi-build-expert/duties.md

## Expert Capabilities
@connsys-experts/framework/experts/framework-common-expert/expert.md
@connsys-experts/wifi/experts/wifi-build-expert/expert.md

@CLAUDE.local.md
```

### 9.3 CLAUDE.local.md（個人客製化）

`CLAUDE.local.md` 放在 workspace 根目錄，不納入 `connsys-experts` repo，供同仁個人客製化：

```markdown
# 個人客製化（CLAUDE.local.md）
- 我偏好用 Python 3.11 做腳本
- 測試環境：172.16.0.x 系列
```

> install.py 在 CLAUDE.md 末尾加入 `@CLAUDE.local.md`，若檔案不存在 Claude Code 會忽略。

---

## 10. 記憶系統設計

### 10.1 四個 Hook 存檔點（Shell 優先實作，project level）

```
存檔可靠性：
1. pre-compact.sh      ← 最可靠（context 壓縮前）
2. mid-checkpoint.sh   ← 每 20 訊息
3. session-end.sh      ← best-effort
4. session-start.sh    ← 載入（不存檔）

複雜邏輯（JSON 解析、記憶壓縮）：呼叫 memory-helper.py
```

Hooks 設定於 project level（`workspace/.claude/settings.json`），由 `setup-claude.sh` 負責寫入，**不由 install.sh 處理**。

### 10.2 connsys-memory Repo 結構（後臺遠端）

```
connsys-memory/ (git)
├── README.md
└── employees/
    ├── john.doe/
    │   ├── sessions/
    │   │   └── 2026-03-23.md
    │   ├── handoffs/
    │   │   └── {run-id}.md
    │   └── summary.md
    └── jane.smith/
```

> **多人衝突**：每人有自己的 `employees/{id}/` 資料夾，帳號不同所以 push 不衝突。同一人多視窗使用時，以 Claude Session ID 為 run-id（詳見 §10.3）確保唯一性。

### 10.3 本地三區記憶（Local Three-Zone Memory）

本地記憶存放於 `workspace/.connsys-expert/memory/{expert-name}/{date}/`，以日期和時間戳命名：

```
workspace/.connsys-expert/memory/
└── wifi-build-expert/
    └── 2026-03-26/
        ├── 10:30-wifi-build-expert-memory.md    ← mid-checkpoint
        └── 17:45-wifi-build-expert-memory.md    ← session-end
```

傳統的三區概念（shared / working / handoffs）改為：

| 用途 | 路徑 | 說明 |
|------|------|------|
| 跨 Expert 共用 | `.connsys-expert/memory/shared/` | project.md, conventions.md 等 |
| 當前 Expert | `.connsys-expert/memory/{expert}/{date}/` | 飛行中狀態，切換時歸檔 |
| 交接文件 | `.connsys-expert/memory/handoffs/{run-id}/` | 寫入後唯讀 |

**session-stop hook** 負責將 `.connsys-expert/memory/` 上傳到遠端 `connsys-memory` repo（git push 同一 repo）。

本地三區的詳細說明（沿用舊設計概念）：

```
workspace/.connsys-expert/memory/
├── shared/                         ← Zone 1：跨 Expert 共用知識（持久）
│   ├── project.md                  ← 專案背景、目標、重要決策
│   ├── conventions.md              ← 跨 Expert 約定的規範
│   └── decisions.md                ← 重要架構決策記錄（ADR）
│
├── working/                        ← Zone 2：當前 Expert 的飛行中狀態（切換時清除）
│   └── wifi-build-expert/          ← 以 expert 名稱為子資料夾
│       └── working.md              ← in-flight 工作日誌、當前進度、未完成項目
│
└── handoffs/                       ← Zone 3：交接文件（寫入後唯讀）
    ├── {session-id}/               ← run-id = Claude Session ID（優先）
    │   └── handoff.md              ← 壓縮摘要 < 2000 tokens
    └── 20260323-160011-a3f2/       ← fallback：{timestamp}-{random4}（Session ID 不可用時）
        └── handoff.md
```

**三個區域的設計原則**：

| 區域 | 生命週期 | 讀寫規則 | 負責 Hook |
|------|---------|---------|---------|
| `shared/` | 長期持久，不因 Expert 切換而清除 | 所有 Expert 可讀寫 | 任何 hook 皆可更新 |
| `working/{expert}/` | 隨 Expert 生命週期，切換時清除（或歸檔） | 僅當前 Expert 寫入，其他可讀 | session-end、pre-compact |
| `handoffs/{run-id}/` | 永久存在，寫入後唯讀 | 由 hand-off hook 建立，後繼 Expert 讀取 | session-end、--switch |

> **run-id 來源**：優先使用 Claude Session ID（確保同一人同時開多個 Claude 視窗不衝突）；若無法取得，fallback 為 `{timestamp}-{random4}`（如 `20260323-160011-a3f2`）。

### 10.4 本地記憶 vs connsys-memory 的分工

```
┌─────────────────────────────────────────────────────────────────┐
│               記憶系統雙層架構                                    │
│                                                                 │
│  本地（workspace/.connsys-expert/memory/）                              │
│  ─────────────────────────────                                  │
│  即時讀寫，Expert 直接存取                                        │
│  • shared/     ← 跨 Expert 知識（環境設定、慣例）                  │
│  • working/    ← 飛行中狀態（進度、筆記、暫存）                    │
│  • handoffs/   ← 交接文件（< 2000 tokens 摘要）                  │
│                                                                 │
│  ↓ session-end / pre-compact hook 定期同步                       │
│                                                                 │
│  遠端（connsys-memory/ git repo）                                 │
│  ─────────────────────────────                                  │
│  後臺收集，跨裝置同步，供 framework-learn-expert 分析              │
│  • sessions/   ← 每次 session 的完整摘要                         │
│  • handoffs/   ← 交接文件備份（與本地 Zone 3 對應）               │
│  • summary.md  ← 滾動式個人知識總覽                              │
└─────────────────────────────────────────────────────────────────┘
```

**為什麼需要本地三區，不直接用 connsys-memory**：
- 本地三區是 Expert 的「工作桌」：即時讀寫，不需 git push，不依賴網路
- connsys-memory 是「歸檔書架」：異步同步，跨裝置，管理者可查閱
- Zone 2（working）設計為「揮發性」：Expert 切換時可以清除，避免記憶污染
- Zone 3（handoffs）設計為「手術室交班記錄」：寫入後不修改，後繼 Expert 信任其內容

### 10.5 週期性記憶收集設計（Lightweight Periodic Collection）

目標：讓記憶能累積供未來 `framework-learn-expert` 分析，同時**不造成即時使用的負擔**。

```
觸發時機（不干擾主流程）：
  1. session-end hook：每次 session 結束時，同步 handoffs/ 到 connsys-memory
  2. mid-session-checkpoint hook：每 20 訊息更新 working/，不 push 到遠端
  3. pre-compact hook：context 壓縮前存快照到 working/，是最可靠的存檔點
  4. 排程同步（未來）：透過 cron 或 CI，每日彙整 working/ + shared/ 到 connsys-memory

輕量化設計原則：
  • 非同步：git push 在背景執行，不阻塞 Expert 的 Think/Plan/Act
  • 增量：只 push 變動的部分，不全量覆寫
  • 限制大小：handoff.md < 2000 tokens；session summary < 5000 tokens
  • 失敗容忍：push 失敗不影響 Expert 繼續工作，下次重試
```

---

## 11. Expert 狀態機與交接流程設計

### 11.1 Expert 工作流程狀態機

每個 Expert 在 `expert.json` 的 `transitions` 中宣告狀態轉移規則。當 Expert 完成工作後，根據結果事件觸發不同的下一步：

```
expert.json（以 wifi-build-expert 為例）：

"transitions": {
  "BUILD_SUCCESS": "wifi-cicd-expert",   ← 成功 → 自動切換到 CI/CD 專家
  "BUILD_FAILED":  null                  ← 失敗 → null 表示需人工介入
}
```

**狀態機圖（wifi-build-expert 為例）**：

```
                     ┌──────────────────────┐
                     │   wifi-build-expert   │
                     │    （活躍中）          │
                     └──────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
         BUILD_SUCCESS    BUILD_FAILED       /handoff（手動）
              │                 │                 │
              ▼                 ▼                 ▼
   ┌──────────────────┐  ┌───────────┐  ┌──────────────────┐
   │  wifi-cicd-      │  │  人工介入  │  │  任意目標 Expert  │
   │  expert          │  │  (null)   │  │  （同仁指定）     │
   │  自動切換         │  │  等待指示  │  │                  │
   └──────────────────┘  └───────────┘  └──────────────────┘
```

**事件來源**：
- Expert 完成任務後，透過 `framework-handoff-flow` skill 主動發出事件
- 事件名稱在 `expert.json` 的 `transitions` 中定義（大寫慣例，如 BUILD_SUCCESS）
- Stage 1 由人工確認後執行 `--switch`；Stage 2 未來可自動觸發

### 11.2 Expert-to-Expert 交接序列圖

```
同仁              wifi-build-expert        install.sh         wifi-cicd-expert
  │                      │                    │                    │
  │── 開始 build 任務 ──►│                    │                    │
  │                      │                    │                    │
  │                 （build 完成）             │                    │
  │                      │                    │                    │
  │◄── BUILD_SUCCESS ───│                    │                    │
  │    建議切換 cicd-expert                   │                    │
  │                      │                    │                    │
  │  [同仁確認切換]        │                    │                    │
  │                      │                    │                    │
  │── source install.sh --switch ──────────►│                    │
  │                      │                    │                    │
  │              ┌────────────────────┐        │                    │
  │              │ hand-off hook 觸發 │        │                    │
  │              │ 1. 更新 working/   │        │                    │
  │              │ 2. 壓縮摘要        │        │                    │
  │              │ 3. 寫 handoffs/   │        │                    │
  │              │ 4. push connsys-memory│      │                    │
  │              └────────────────────┘        │                    │
  │                      │                    │                    │
  │                      │── 清除 working/ ──►│                    │
  │                      │                    │── 重建 symlinks ──►│
  │                      │                    │── 更新 CLAUDE.md ─►│
  │                      │                    │                    │
  │◄──────────────────── ✅ 安裝完成 ──────────────────────────────│
  │                      │                    │                    │
  │── 重新開啟 Claude Code ──────────────────────────────────────►│
  │                                                               │
  │                                              ┌────────────────────┐
  │                                              │ session-start hook │
  │                                              │ 1. 讀 handoffs/   │
  │                                              │ 2. 讀 shared/     │
  │                                              │ 3. 注入 context   │
  │                                              └────────────────────┘
  │                                                               │
  │◄── 「接到 wifi-build-expert 的工作：BUILD_SUCCESS，任務是...」──│
  │                                                               │
  │── 繼續任務 ───────────────────────────────────────────────►  │
```

### 11.3 session-start.sh：交接上下文注入

`session-start.sh` 是 Expert 啟動的第一件事，負責將交接資訊注入新的 Expert session。
採用 **Shell 優先**策略：基本邏輯用 Shell，複雜的 JSON 解析或記憶壓縮呼叫 `memory-helper.py`。

```bash
#!/usr/bin/env bash
# session-start.sh
# Claude Code hook：session 開始時載入交接文件與共用記憶

MEMORY_DIR="${CONNSYS_EXPERTS_WORKSPACE_ROOT_PATH}/.claude/memory"
HANDOFFS_DIR="${MEMORY_DIR}/handoffs"
SHARED_DIR="${MEMORY_DIR}/shared"

# 1. 偵測是否有待接的 hand-off（取最新一筆）
latest_handoff=$(ls -t "${HANDOFFS_DIR}"/*/handoff.md 2>/dev/null | head -1)

# 2. 輸出交接文件內容（Claude Code hook 透過 stdout 注入 context）
if [[ -f "${latest_handoff}" ]]; then
  echo "## 來自上一個 Expert 的交接"
  cat "${latest_handoff}"
  echo ""
fi

# 3. 載入共用記憶
if [[ -f "${SHARED_DIR}/project.md" ]]; then
  echo "## 專案共用知識"
  cat "${SHARED_DIR}/project.md"
  echo ""
fi

if [[ -f "${SHARED_DIR}/conventions.md" ]]; then
  echo "## 跨 Expert 約定"
  cat "${SHARED_DIR}/conventions.md"
  echo ""
fi

# 4. 複雜邏輯交給 Python helper（例如：解析 handoff YAML frontmatter、更新已讀標記）
HELPER="${CONNSYS_EXPERTS_PATH}/framework/experts/framework-common-expert/hooks/memory-helper.py"
if [[ -f "${HELPER}" ]]; then
  python3 "${HELPER}" mark-handoff-read "${latest_handoff}" 2>/dev/null || true
fi
```

> `memory-helper.py` 完整實作（含 PEP 723 inline metadata）見 **§8.4**。

**為什麼這個設計是必要的**（對應 v1 設計 gap 分析）：
- v1 設計有 `run-agent.sh`，啟動時注入 handoff context
- v2 補回此功能，改以 Claude Code hook 實作（`session-start.sh`）
- 本地 `handoffs/` 存在，新 Expert 不需要去 connsys-memory 拉取，降低啟動延遲
- Shell/Python 雙層設計：Shell 負責流程控制，Python 負責結構化資料操作

### 11.4 hand-off 文件寫入時機與存放位置

| 觸發事件 | 本地寫入 | 遠端同步 |
|---------|---------|---------|
| `--switch`（切換 Expert）| `memory/handoffs/{run-id}/handoff.md` | `connsys-memory/employees/{id}/handoffs/` |
| `session-end`（對話結束）| `memory/handoffs/{run-id}/handoff.md` | `connsys-memory/employees/{id}/handoffs/` |
| `/handoff`（手動指令）| `memory/handoffs/{run-id}/handoff.md` | 可選（手動 push）|
| `pre-compact`（context 壓縮）| `memory/working/{expert}/working.md` | 不同步（工作草稿）|

---

## 12. Hand-off 文件格式

```markdown
---
schema: handoff-v1
run_id: "20260323-143022"
from: wifi-build-expert
to: wifi-cicd-expert
status: BUILD_SUCCESS
timestamp: "2026-03-23T14:30:22Z"
domain: wifi
employee_id: john.doe
---

## 任務摘要
成功編譯 bora fw，make all 通過，artifact 位於 fw/bora/build/out/。

## 關鍵發現
- 編譯指令：`make -C $CONNSYS_EXPERTS_CODE_SPACE_PATH/fw/bora/build all -j8`
- 輸出目錄：`fw/bora/build/out/`
- 特別注意：需先 source setup.sh

## 建議下一步
1. 執行 CI/CD pipeline
2. push 前確認 remote 分支（需人工確認）
```

---

## 13. 安全與權限設計

| 考量 | 設計 |
|------|------|
| **客戶資料隔離** | 客戶相關資料（manifest、設定、credentials）存於**獨立 git repo**，不放入 `connsys-experts` |
| **無客戶名稱** | `connsys-experts` 所有 SKILL.md / CLAUDE.md 內容均不含客戶名稱 |
| **權限管理** | 依 domain 分資料夾，方便對不同 domain 設定不同的 git access control |
| **安全掃描** | domain 層級的清楚分隔，方便對 wifi / bt / system 各自執行 secret scan |
| **命名不衝突** | Layer 1-5 的命名規則確保全域唯一（domain prefix + type postfix）|
| **External 隔離** | 外部工具放 `external-experts/`，與 internal 清楚分開，方便掃描外部依賴 |

---

## 13.5 已知限制

| 限制 | 說明 | 對應 Future Work |
|------|------|-----------------|
| **Skill 版本向後相容** | SKILL.md `version` 欄位僅供顯示，Skill 升版後舊 hand-off 文件的相容性未定義；breaking change 需人工審查 | 無（列為設計邊界） |
| **Local Memory 無 GC** | `memory/shared/`、`memory/handoffs/` 無自動清理機制，長期使用後可能無限增長 | FW-04 |
| **registry.json 格式未定義** | `registry.json` 存在但格式尚未設計，expert-discovery skill 目前僅能手動列表 | FW-05 |
| **connsys-memory 同帳號多開衝突** | 同一人同時開多個 Claude 視窗時，若 Session ID 無法取得，timestamp fallback 仍有極小衝突機率 | FR-06-9（優先用 Session ID）|
| **Windows symlink** | Windows 不支援 symlink，install.py 自動降級為 copy 模式；copy 模式下更新 expert 內容後需重新執行 install.py | 無（自動處理）|
| **Human in the Loop 無超時機制** | 目前 HitL 確認行為由 prompt 驅動，無自動超時或「不再詢問」機制 | Phase 2 設計 |

---

## 14. 遷移路線

### 14.1 三階段遷移

| 機制 | Phase 1：Claude Code | Phase 2：OpenClaw | Phase 3：ADK/SDK |
|------|---------------------|------------------|-----------------|
| 安裝 | `install.sh` symlink | `install.sh --target openclaw` | `AgentDefinition` 自動 |
| Hooks | **Shell（優先）+ Python（複雜邏輯）** | TypeScript `handler.ts`（此階段重寫）| `PostToolUse callback` |
| Skills | SKILL.md | SKILL.md + `metadata.openclaw` | `system_prompt` 注入 |
| Commands | COMMAND.md（相容層，Phase 1 不新增）| user-invocable Skill | SDK tool 定義 |
| Memory | Markdown + Git | MEMORY.md + LanceDB | JSON output |
| Human in Loop | 手動確認 | Hook 觸發確認 | 風險評分自動決定 |

### 14.2 Skill 與 Command 的邊界設計

**原則**：**Skill 是主要實作單位，`commands/` 資料夾為 Claude plugin format 的相容層**。Phase 1 新開發的 Expert 不需建立獨立的 command 資料夾。

| 情況 | 做法 |
|------|------|
| 需要自動觸發的知識/流程 | 使用 Skill，不加 `disable-model-invocation` |
| 需要像 Command 一樣由使用者主動呼叫 | 使用 Skill，在 SKILL.md frontmatter 加 `disable-model-invocation: true` |
| 已有 `commands/` 資料夾的 Expert | 保留（相容），不主動遷移，Phase 2 統一處理 |
| 新建 Expert | 只用 Skill，不建 commands/ |

**`disable-model-invocation` 範例**：

```yaml
---
name: framework-handoff-tool
type: tool
disable-model-invocation: true   # 使用者主動輸入 /handoff 才觸發，不自動觸發
description: 手動觸發 hand-off 交接流程
---
```

### 14.3 SKILL.md 遷移格式

加入 `metadata.openclaw` 區塊即可，內容不需修改：

```yaml
---
name: wifi-build-flow
# ... 現有欄位不變 ...
metadata:
  openclaw:
    emoji: "🔨"
    always: false
    user-invocable: false
---
```

---

## 15. 名詞定義

| 術語 | 定義 |
|------|------|
| Domain | 技術領域分類（framework / wifi / bt / system） |
| `{domain}-common-expert` | 存放該 domain 共用 skill/hook 的容器，install.sh 無作用 |
| `framework-common-expert` | 存放跨所有 domain 共用 skill/hook 的容器 |
| `flow` skill | 有清楚步驟的工作流程 SOP |
| `knowhow` skill | 基礎知識與背景資料 |
| `tool` skill | 外部工具的操作方法 |
| Layer 1-5 | connsys-experts 的五層資料夾命名規則 |
| `CONNSYS_EXPERTS_WORKSPACE_ROOT_PATH` | workspace 根目錄，`.claude/` 所在 |
| `CONNSYS_EXPERTS_CODE_SPACE_PATH` | 程式碼路徑（兩個場景值不同） |
| Human in the Loop | 對高風險操作暫停等待人類確認的機制 |
| Local Three-Zone Memory | 本地三區記憶：`shared/`（持久共用）+ `working/`（飛行中）+ `handoffs/`（交接文件） |
| `memory/shared/` | 跨 Expert 共用知識，Expert 切換後持續存在 |
| `memory/working/{expert}/` | 當前 Expert 的飛行中工作狀態，切換時清除 |
| `memory/handoffs/{run-id}/` | Expert 交接摘要（< 2000 tokens），寫入後唯讀 |
| transitions | `expert.json` 中定義的事件→下一個 Expert 狀態機轉移規則 |
| connsys-memory | 後臺遠端 git repo，供跨裝置同步與 framework-learn-expert 分析 |

---

## 16. Future Work

### 16.1 Security：Expert 安全審計機制

**動機**：

AI Agent 生態系統的成長速度遠超其安全工具：
- 2026 年 1 月，一個主要 Agent 技能市場的 **12% 技能為惡意**（2,857 個社區技能中有 341 個惡意）
- 一個 **CVSS 8.8** 的 CVE 暴露了 17,500+ 個面向網路的實例
- Moltbook 漏洞跨 770,000 個 Agent 洩露了 **150 萬個 API token**

**現況問題**：

同仁在安裝社區技能（external-experts）、連接 MCP 伺服器、配置 hooks 時，沒有任何自動化方式來審計設定的安全性。

**目標**：

建立 `framework-security-expert`，提供以下能力：

```
framework/experts/
└── framework-security-expert/
    ├── skills/
    │   ├── framework-security-audit-flow/     ← 審計流程 SOP
    │   │   └── SKILL.md
    │   ├── framework-skill-scan-tool/         ← 掃描已安裝 skills 的安全性
    │   │   └── SKILL.md
    │   ├── framework-hook-scan-tool/          ← 掃描 hooks 是否有惡意行為
    │   │   └── SKILL.md
    │   └── framework-supply-chain-knowhow/    ← 供應鏈攻擊知識
    │       └── SKILL.md
    ├── hooks/
    │   └── pre-install-check.sh               ← 安裝前自動掃描
    ├── commands/
    │   └── framework-security-audit-tool/     ← /security-audit 指令
    │       └── COMMAND.md
    ├── test/
    └── report/
```

**設計方向**（參考 AgentShield）：

| 功能 | 說明 |
|------|------|
| 靜態分析 | 掃描 SKILL.md / COMMAND.md 是否有 prompt injection、資料外洩指令 |
| Hook 掃描 | 檢查 `.sh` / `.py` hooks 是否有可疑的網路呼叫、檔案讀寫 |
| External 審計 | 安裝 external-experts 前，比對已知惡意 skill fingerprint |
| Pre-install hook | 在 install.sh 執行前觸發安全檢查，阻止高風險安裝 |
| 報告產生 | 自動更新 `report/execution-report.md`，記錄安全掃描結果 |

**參考實作**：[AgentShield](https://github.com/affaan-m/agentshield)

---

### 16.2 Memory + Learn：自我檢討的 Expert

**動機**：

目前 Expert 的 knowledge（SKILL.md）是靜態的，由人工撰寫和維護。未來希望 Expert 能**從使用記憶中自動學習**，持續改善自己的 skills。

**設計方向**：

```
使用記憶（connsys-memory/employees/{id}/sessions/）
    ↓ framework-learn-expert 分析
找出 pattern（常見錯誤、成功解法、反覆遇到的問題）
    ↓
自動產生或更新 SKILL.md（howknow / flow 類型）
    ↓
framework-skill-create-expert 驗證格式
    ↓
PR 給人工 review → merge → 所有人受益
```

**三個層次的記憶演進**：

| 層次 | 機制 | 實作 |
|------|------|------|
| **短期**：session 記憶 | session-end hook 自動儲存 | 已實作（claude-memory-engine 模式）|
| **中期**：跨 session 學習 | framework-learn-expert 定期分析 sessions/ | 未來工作 |
| **長期**：知識固化 | 分析結果→新增/更新 SKILL.md→PR | 未來工作 |

**`framework-learn-expert` 強化方向**：

```
framework/experts/framework-learn-expert/skills/
├── framework-learn-flow/           ← 分析記憶→找 pattern 的 SOP
│   └── SKILL.md
├── framework-feedback-knowhow/     ← 如何從錯誤記錄中萃取知識
│   └── SKILL.md
└── framework-skill-improve-flow/   ← 自動產生 skill PR 的流程（新增）
    └── SKILL.md
```

**目標效果**：Expert 不只是靜態知識庫，而是能透過累積的使用資料**持續自我強化**的系統，實現真正的 `Think → Plan → Act → Learn` 循環。

**參考實作**：[claude-mem](https://github.com/thedotmack/claude-mem)

---

### 16.3 Skill README 開發說明範本

**現況**：Skill README.md 的開發說明章節目前無標準格式，各 Skill 寫法不一致。

**目標**：提供統一的 Skill README 範本，包含：如何新增 case、測試覆蓋率目標、已知問題記錄方式，由 `framework-skill-create-expert` 在建立新 Skill 時自動生成。

**參考資料**：

- [Skill Best Practices（Claude 官方）](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [SKILL.md 範例（Anthropic skills repo）](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)

> 待真實使用後再補齊完整範本與步驟說明。

---

### 16.4 Local Memory GC 機制

**現況**：`memory/shared/`、`memory/handoffs/` 無自動清理，長期使用後可能無限增長。

**設計方向**：

| 區域 | GC 策略 |
|------|---------|
| `memory/handoffs/` | 保留最近 N 個 run-id（建議 30），超出者歸檔至 connsys-memory |
| `memory/shared/` | 超過閾值（如 100KB）時，由 session-end hook 呼叫 Python helper 自動摘要壓縮 |
| `memory/working/` | Expert 切換時清除（已有設計），無需額外 GC |

> 待真實使用 hand-off 功能、累積足夠資料後再行實作。

---

### 16.5 registry.json 格式與 Expert 推薦

**現況**：`registry.json` 規格未定義，`expert-discovery` skill 僅能手動列表，無根據任務自動推薦的能力。

**設計方向**：

```json
// registry.json（草案格式）
{
  "version": "1.0",
  "experts": [
    {
      "name": "wifi-build-expert",
      "path": "wifi/experts/wifi-build-expert",
      "description": "負責 WiFi 韌體 Build 流程",
      "tags": ["build", "wifi", "compile"],
      "owner": "wifi-team"
    }
  ]
}
```

> 待開始實際使用多 Expert 後再行設計；registry.json 可由 CI 自動從各 expert.json aggregate。

---

## 17. 參考資料

### 核心概念

| 資料 | 說明 |
|------|------|
| [Harness Engineering（Martin Fowler Blog）](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html) | 本系統架構的核心啟發：為 AI 打造自動化治理體系 |
| [AgentShield](https://github.com/affaan-m/agentshield) | Agent 生態系統安全審計參考實作 |
| [claude-memory-engine](https://github.com/HelloRuru/claude-memory-engine) | 8-step 學習循環記憶引擎，hooks 設計參考 |
| [claude-mem](https://github.com/thedotmack/claude-mem) | 輕量記憶系統，memory → learn 機制參考 |

### 技術文件

| 資料 | 說明 |
|------|------|
| [Claude Plugin 文件](https://code.claude.com/docs/en/plugins) | Expert 資料夾結構參考（skills/hooks/commands 格式）|
| [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) | Skill 資料夾設計參考 |

### 延伸閱讀（個人知識庫，連結待更新）

| 資料 | 說明 |
|------|------|
| [Lessons from Building Claude Code — How We Use Skills](https://github.com/swchen44/personal-knowledge-base-from-ai/blob/main/AI/2026-03-17-LESSONS-FROM-BUILDING-CLAUDE-CODE-HOW-WE-USE-SKILLS.md) | 實戰經驗：Claude Code 中 Skills 的使用心得 |
| [5 Agent Skill Design Patterns Every ADK Developer Should Know](https://github.com/swchen44/personal-knowledge-base-from-ai/blob/main/AI/2026-03-18-5-AGENT-SKILL-DESIGN-PATTERNS-EVERY-ADK-DEVELOPER-SHOULD-KNOW.md) | ADK 開發者必知的 5 種 Skill 設計模式 |
| [Claude-mem Code Analysis](https://github.com/swchen44/personal-knowledge-base-from-ai/blob/main/CodeAnalysis/2025-08-31-CLAUDE-MEM-CODE-ANALYSIS.md) | claude-mem 原始碼深度分析 |
