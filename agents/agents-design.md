# Consys Experts — 設計書

**文件版本**：v2.3
**狀態**：Draft
**依據**：agents-requirements.md v2.1

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
│  垃圾回收    session-end 整理記憶 / push consys-memory              │
│                                                                     │
│         ↓ 透過以上三層強化 AI 核心能力（Think/Plan/Act/Learn）       │
│                                                                     │
│     Claude Code（現在）→ OpenClaw（Phase 2）→ ADK/SDK（Phase 3）    │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Consys Expert 組成

```
Consys Expert = Agent 核心能力 + Workflow（hooks）+ Tool（commands）+ Knowledge（skills）

每個 Expert 的內容分三個來源：
  ① framework-common-expert  → 跨所有 domain 共用
  ② {domain}-common-expert   → 該 domain 內部共用
  ③ {expert} private         → 該 Expert 自己的私有內容

全部透過 symlink 接入 workspace/.claude/（project level）
```

---

## 2. 五層資料夾設計（Layer 1–5）

### 2.1 層次總覽

```
consys-experts/
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
│   │       ├── unittest/
│   │       ├── report/
│   │       │   ├── execution-report.md    ← 人工維護
│   │       │   └── unittest-report.md     ← 人工維護
│   │       ├── README.md
│   │       ├── install.sh
│   │       ├── expert.json
│   │       └── CLAUDE.md
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

每個 expert（除 common-expert 外）的資料夾結構：

```
{expert}/
├── README.md              ← 說明此 expert 的用途、能力、使用方式
├── install.sh             ← 安裝腳本（依 expert.json 建立 symlinks）
├── expert.json            ← Expert 設定（含 dependencies 宣告）
├── CLAUDE.md              ← 此 Expert 的 system prompt 模板
│
├── skills/                ← Knowledge：多個 skill 資料夾
│   └── {domain}-{name}-{type}/
│       └── SKILL.md
│
├── hooks/                 ← Workflow：針對此 expert 的額外 hook（可選）
│   └── {hook-name}.js     ← Claude Code 實作（project level）
│
├── commands/              ← Tool：多個 command 資料夾
│   └── {domain}-{name}-tool/
│       └── COMMAND.md
│
├── unittest/              ← 預留：skill / hook 的測試腳本
│
└── report/                ← 預留：人工維護的報告
    ├── execution-report.md
    └── unittest-report.md
```

**`{domain}-common-expert` 的資料夾結構**（同上，但 install.sh 無作用）：

```
{domain}-common-expert/
├── README.md
├── install.sh             ← 無作用（common 不直接安裝）
├── expert.json            ← 僅描述，無 dependencies
├── skills/                ← 此 domain 共用的 skills
├── hooks/                 ← 此 domain 共用的 hooks（可選）
├── commands/              ← 此 domain 共用的 commands（可選）
├── unittest/
└── report/
```

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
framework-memory-tool                ← consys-memory 操作

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
consys-experts/ (git)
├── README.md
├── registry.json                            ← 全域 Expert 目錄
├── install.sh                               ← 頂層：env vars + clone consys-memory
│
├── framework/
│   ├── experts/
│   │   ├── framework-common-expert/         ← 跨所有 domain 共用（install.sh 無作用）
│   │   │   ├── README.md
│   │   │   ├── install.sh                   ← 無作用
│   │   │   ├── expert.json
│   │   │   ├── skills/
│   │   │   │   ├── framework-expert-discovery-knowhow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   ├── framework-handoff-flow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   └── framework-memory-tool/
│   │   │   │       └── SKILL.md
│   │   │   ├── hooks/                       ← 所有 Expert 共用的 hooks（Claude Code 實作）
│   │   │   │   ├── session-start.js
│   │   │   │   ├── session-end.js
│   │   │   │   ├── pre-compact.js
│   │   │   │   ├── mid-session-checkpoint.js
│   │   │   │   └── shared-utils.js
│   │   │   ├── commands/
│   │   │   │   ├── framework-experts-tool/
│   │   │   │   │   └── COMMAND.md
│   │   │   │   └── framework-handoff-tool/
│   │   │   │       └── COMMAND.md
│   │   │   ├── unittest/
│   │   │   └── report/
│   │   │       ├── execution-report.md
│   │   │       └── unittest-report.md
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
│   │   │   ├── unittest/
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
│   │       ├── unittest/
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
│   │   │   ├── unittest/
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
│   │   │   ├── unittest/
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
│   │   │   ├── unittest/
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
│   │       ├── unittest/
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
│   │   │   ├── unittest/
│   │   │   └── report/
│   │   ├── bt-build-expert/                 ← 【示例】
│   │   │   ├── skills/
│   │   │   │   ├── bt-build-flow/
│   │   │   │   │   └── SKILL.md
│   │   │   │   └── bt-fw-build-flow/        ← bt fw 完整 build 流程
│   │   │   │       └── SKILL.md
│   │   │   ├── hooks/ ├── commands/ ├── unittest/ └── report/
│   │   └── bt-debug-expert/                 ← 【示例】
│   │       ├── skills/ ├── hooks/ ├── commands/ ├── unittest/ └── report/
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
    │   │   ├── hooks/ ├── commands/ ├── unittest/ └── report/
    │   ├── system-cicd-expert/              ← 【示例】
    │   │   ├── skills/ ├── hooks/ ├── commands/ ├── unittest/ └── report/
    │   └── system-device-expert/            ← 【示例】
    │       ├── skills/ ├── hooks/ ├── commands/ ├── unittest/ └── report/
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
        "wifi-coderule-knowhow",
        "wifi-gerrit-tool",
        "wifi-repo-tool"
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
  "description": "wifi domain 共用 skill/hook/command 的容器，不直接安裝",
  "version": "1.0.0",
  "is_common": true,
  "install_action": "none"
}
```

---

## 5. install.sh 設計

### 5.1 參數定義

```bash
source {domain}/experts/{expert}/install.sh [OPTIONS]

OPTIONS:
  （無參數）          安裝此 Expert（symlink 模式，自動偵測場景）
  --copy              安裝（複製模式）
  --uninstall         移除當前 Expert 的所有 links
  --switch            切換（= uninstall + install + 印出 diff）
  --target openclaw   安裝目標為 OpenClaw（未來）
  --scenario VALUE    指定場景：agent-first 或 legacy
  --env-only          僅設定環境變數
```

### 5.2 install.sh 的 Symlink 建立邏輯

install.sh 讀取 `expert.json` 的 `dependencies` + `private`，依序在 workspace `.claude/` 建立 symlinks：

```
安裝 wifi-build-expert 時的 .claude/ 結果：

.claude/
├── skills/
│   ├── framework-expert-discovery-knowhow  → $CONSYS_EXPERTS_PATH/framework/experts/framework-common-expert/skills/framework-expert-discovery-knowhow/
│   ├── framework-handoff-flow              → $CONSYS_EXPERTS_PATH/framework/experts/framework-common-expert/skills/framework-handoff-flow/
│   ├── framework-memory-tool               → $CONSYS_EXPERTS_PATH/framework/experts/framework-common-expert/skills/framework-memory-tool/
│   ├── wifi-protocol-knowhow               → $CONSYS_EXPERTS_PATH/wifi/experts/wifi-common-expert/skills/wifi-protocol-knowhow/
│   ├── wifi-arch-knowhow                   → $CONSYS_EXPERTS_PATH/wifi/experts/wifi-common-expert/skills/wifi-arch-knowhow/
│   ├── wifi-gerrit-tool                    → $CONSYS_EXPERTS_PATH/wifi/experts/wifi-common-expert/skills/wifi-gerrit-tool/
│   ├── wifi-build-flow                     → $CONSYS_EXPERTS_PATH/wifi/experts/wifi-build-expert/skills/wifi-build-flow/
│   └── wifi-builderror-knowhow             → $CONSYS_EXPERTS_PATH/wifi/experts/wifi-build-expert/skills/wifi-builderror-knowhow/
│
├── hooks/                                  ← 來自 framework-common-expert（Claude Code 實作）
│   ├── session-start.js          → $CONSYS_EXPERTS_PATH/framework/experts/framework-common-expert/hooks/session-start.js
│   ├── session-end.js            → .../framework-common-expert/hooks/session-end.js
│   ├── pre-compact.js            → .../framework-common-expert/hooks/pre-compact.js
│   ├── mid-session-checkpoint.js → .../framework-common-expert/hooks/mid-session-checkpoint.js
│   └── shared-utils.js           → .../framework-common-expert/hooks/shared-utils.js
│
└── commands/
    ├── framework-experts-tool    → .../framework-common-expert/commands/framework-experts-tool/
    └── framework-handoff-tool    → .../framework-common-expert/commands/framework-handoff-tool/
```

### 5.3 切換 Expert 時的 diff 輸出

```
$ source wifi/experts/wifi-cicd-expert/install.sh --switch

🔄 切換 Expert: wifi-build-expert → wifi-cicd-expert
💾 儲存 wifi-build-expert 工作記憶...

Skills 變更：
  ✓ 新增: wifi-cicd-flow, wifi-preflight-tool, wifi-autotest-tool
  ✗ 移除: wifi-build-flow, wifi-builderror-knowhow, wifi-linkerscript-knowhow, wifi-rompatch-knowhow
  ○ 保留: framework-expert-discovery-knowhow, framework-handoff-flow
  ○ 保留: wifi-protocol-knowhow, wifi-arch-knowhow, wifi-gerrit-tool, wifi-repo-tool

Hooks 變更：
  ○ 保留（framework-common）: session-start, session-end, pre-compact, mid-session-checkpoint

Commands 變更：
  ○ 保留（framework-common）: /experts, /handoff

✅ wifi-cicd-expert 安裝完成，請重新開啟 Claude Code
```

---

## 6. 環境變數設計

install.sh 透過 `source` 設定，供所有 Expert 的 workflow / tool / knowledge 使用。
所有變數統一使用 `CONSYS_EXPERTS_` 前綴：

```bash
export CONSYS_EXPERTS_PATH="..."                              # consys-experts repo 路徑
export CONSYS_EXPERTS_WORKSPACE_ROOT_PATH="$(pwd)"           # workspace 根目錄（.claude/ 所在）
export CONSYS_EXPERTS_CODE_SPACE_PATH="..."                  # 程式碼路徑（agent-first: codespace/；legacy: workspace root）
export CONSYS_EXPERTS_MEMORY_PATH="$(pwd)/consys-memory"     # consys-memory repo 路徑
export CONSYS_EXPERTS_EMPLOYEE_ID="$(git config user.name)"  # 員工工號
```

| 變數 | Agent First | Legacy |
|------|-------------|--------|
| `CONSYS_EXPERTS_WORKSPACE_ROOT_PATH` | `~/workspace` | `~/workspace` |
| `CONSYS_EXPERTS_CODE_SPACE_PATH` | `~/workspace/codespace` | `~/workspace` |

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
cd $CONSYS_EXPERTS_CODE_SPACE_PATH
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

## 8. CLAUDE.md 生成機制

install.sh 在 `$CONSYS_EXPERTS_WORKSPACE_ROOT_PATH` 生成 `CLAUDE.md`：

```markdown
# Consys Expert: WiFi Build Expert

@.claude/expert.md
@.claude/expert.local.md
```

`expert.md`（由 install.sh 從 expert.json 生成）：

```markdown
# WiFi Build Expert

**Domain**：wifi
**描述**：專門處理 Wi-Fi 韌體下載、編譯與 build error 排查

## 已載入的技能（Knowledge）
- framework-expert-discovery-knowhow
- framework-handoff-flow
- wifi-protocol-knowhow, wifi-arch-knowhow, wifi-coderule-knowhow
- wifi-build-flow, wifi-builderror-knowhow, wifi-linkerscript-knowhow

## 觸發情境
build, compile, 編譯, BUILD_FAILED

## 環境資訊
- Workspace: $CONSYS_EXPERTS_WORKSPACE_ROOT_PATH
- Code Space: $CONSYS_EXPERTS_CODE_SPACE_PATH

## 個人客製化
如需客製化，請建立 `.claude/expert.local.md`（不納入 repo）。
```

---

## 9. 記憶系統設計

### 9.1 四個 Hook 存檔點（Claude Code 實作，project level）

```
存檔可靠性：
1. pre-compact     ← 最可靠（context 壓縮前）
2. mid-checkpoint  ← 每 20 訊息
3. session-end     ← best-effort
4. session-start   ← 載入（不存檔）
```

Hooks 設定於 project level（`workspace/.claude/settings.json`），由 `setup-claude.sh` 負責寫入，**不由 install.sh 處理**。

### 9.2 consys-memory Repo 結構

```
consys-memory/ (git)
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

---

## 10. Hand-off 文件格式

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
- 編譯指令：`make -C $CONSYS_EXPERTS_CODE_SPACE_PATH/fw/bora/build all -j8`
- 輸出目錄：`fw/bora/build/out/`
- 特別注意：需先 source setup.sh

## 建議下一步
1. 執行 CI/CD pipeline
2. push 前確認 remote 分支（需人工確認）
```

---

## 11. 安全與權限設計

| 考量 | 設計 |
|------|------|
| **客戶資料隔離** | 客戶相關資料（manifest、設定、credentials）存於**獨立 git repo**，不放入 `consys-experts` |
| **無客戶名稱** | `consys-experts` 所有 SKILL.md / CLAUDE.md 內容均不含客戶名稱 |
| **權限管理** | 依 domain 分資料夾，方便對不同 domain 設定不同的 git access control |
| **安全掃描** | domain 層級的清楚分隔，方便對 wifi / bt / system 各自執行 secret scan |
| **命名不衝突** | Layer 1-5 的命名規則確保全域唯一（domain prefix + type postfix）|
| **External 隔離** | 外部工具放 `external-experts/`，與 internal 清楚分開，方便掃描外部依賴 |

---

## 12. 遷移路線

### 12.1 三階段遷移

| 機制 | Phase 1：Claude Code | Phase 2：OpenClaw | Phase 3：ADK/SDK |
|------|---------------------|------------------|-----------------|
| 安裝 | `install.sh` symlink | `install.sh --target openclaw` | `AgentDefinition` 自動 |
| Hooks | JS，project level | TypeScript `handler.ts` | `PostToolUse callback` |
| Skills | SKILL.md | SKILL.md + `metadata.openclaw` | `system_prompt` 注入 |
| Commands | COMMAND.md | user-invocable Skill | SDK tool 定義 |
| Memory | Markdown + Git | MEMORY.md + LanceDB | JSON output |
| Human in Loop | 手動確認 | Hook 觸發確認 | 風險評分自動決定 |

### 12.2 SKILL.md 遷移格式

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

## 13. 名詞定義

| 術語 | 定義 |
|------|------|
| Domain | 技術領域分類（framework / wifi / bt / system） |
| `{domain}-common-expert` | 存放該 domain 共用 skill/hook 的容器，install.sh 無作用 |
| `framework-common-expert` | 存放跨所有 domain 共用 skill/hook 的容器 |
| `flow` skill | 有清楚步驟的工作流程 SOP |
| `knowhow` skill | 基礎知識與背景資料 |
| `tool` skill | 外部工具的操作方法 |
| Layer 1-5 | consys-experts 的五層資料夾命名規則 |
| `CONSYS_EXPERTS_WORKSPACE_ROOT_PATH` | workspace 根目錄，`.claude/` 所在 |
| `CONSYS_EXPERTS_CODE_SPACE_PATH` | 程式碼路徑（兩個場景值不同） |
| Human in the Loop | 對高風險操作暫停等待人類確認的機制 |
