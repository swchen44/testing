# Consys Harness Experts — 需求書

**文件版本**：v2.0
**狀態**：Draft
**目標讀者**：架構師、開發者、產品負責人
**改版說明**：v2.0 以使用者故事為主軸重寫，完整記錄設計決策的「為什麼」

---

## 1. 背景與目標

### 1.1 問題陳述

韌體開發團隊的日常工作涉及多個 repo 的下載、編譯、修復、上傳與裝置控制。目前工作流程完全依賴人工判斷，導致以下痛點：

- 每位同仁對工具鏈的熟悉程度不同，重複踩坑
- AI 輔助工具（Claude Code）的使用方式因人而異，效益不一致
- Agent 與 Agent 之間的上下文無法有效傳遞（Context 爆炸問題）
- 無法收集使用資料，難以知道哪些流程需要改善

### 1.2 目標

建立一套以 **Claude Code** 為執行環境、可跨平台遷移的 **Expert 系統**，達成：

1. 同仁可快速安裝對應領域的「專家」(Expert)，取得即用的 Skills、Hooks 與 Commands
2. Expert 之間透過結構化 Hand-off 傳遞上下文，避免 Context 爆炸
3. 使用資料自動收集至後臺 Git repo，供反思與大數據分析
4. 架構不綁定特定 AI 平台，未來可平滑遷移至 OpenClaw 或 ADK/SDK

### 1.3 為什麼選擇這個架構方向

| 設計決策 | 理由 |
|---------|------|
| 獨立的 `consys-harness-experts` repo | Expert 工具與 source code 分開管理，兩者生命週期不同；同仁可在任何 workspace 安裝 |
| 以 symlink 為預設安裝方式 | 切換 Expert 時直接重建 link 即可，無需處理檔案複製的一致性問題；copy 模式保留作為選項以應對特殊需求 |
| CLAUDE.md 採覆蓋（替換）策略 | 切換 Expert 等於「換一個專家來做事」——新專家帶來全新的技能組合，不應保留前一個 Expert 的設定 |
| install.sh 不觸碰 settings.json | settings.json 屬於平台設定（Claude vs OpenClaw），應由獨立的 `setup-claude.sh` 處理，降低 install.sh 與平台的耦合 |
| 記憶系統用 Markdown + Git | 不需外部資料庫，完全透明可編輯，天然支援跨裝置同步與版本稽核 |
| 工號（git username）作為後臺資料夾名稱 | 無需額外帳號系統，git 帳號即工號，install.sh 可自動取得 |
| `external/` 資料夾 | 避免重造輪子，整合社群優秀工具（如 skill-creator、claude-memory-engine），以工具名稱為資料夾名，清楚標示來源 |

---

## 2. 使用者故事

### US-01：Agent First 場景（從空白 workspace 開始）

**背景**：同仁拿到一台新機器，workspace 是空的，想用 Expert 輔助下載並編譯韌體。

**流程**：
```
1. 同仁在 ~/workspace/ 執行 Claude Code
2. 手動 clone consys-harness-experts
3. 查看 experts/ 下有哪些 Expert，選擇 build-expert
4. 執行 source experts/build-expert/install.sh
5. 開啟 Claude Code → 已具備 build-expert 的 Skills/Hooks/Commands
6. 與 Claude 互動，Claude 協助用 repo tool 下載 fw 到 codespace/fw/
7. 需要切換到 cicd-expert 時，執行 install.sh --switch，看到切換清單後確認
```

**驗收條件**：
- install.sh 執行後，`.claude/skills/`、`.claude/hooks/`、`.claude/commands/` 均正確建立 symlink
- `CLAUDE.md` 被生成，內容 @include `expert.md` 與 `expert.local.md`
- 環境變數 `CONSYS_EXPERTS_PATH`、`CONSYS_CODE_SPACE_PATH` 設定完成
- `consys-memory/` repo 被自動 clone，員工資料夾以 git username 命名

---

### US-02：Legacy 場景（已手動下載 code）

**背景**：同仁已用 `repo` 工具按照傳統流程下載好 fw，現在想引入 Expert 輔助。

**流程**：
```
1. 同仁已有：
   ~/workspace/.repo
   ~/workspace/bora/wifi, bt, mcu, build, coexistence (各為獨立 git repo)
2. 在 ~/workspace/ clone consys-harness-experts
3. 執行 source experts/build-expert/install.sh --scenario legacy
4. install.sh 自動偵測到 .repo 存在，判斷為 legacy 場景
5. 建立 .claude/ symlinks，生成 CLAUDE.md
6. 開啟 Claude Code，既有 code 與新安裝的 Expert 技能整合運作
```

**驗收條件**：
- install.sh 能自動偵測場景（legacy vs agent-first）
- Legacy 場景的 `CONSYS_CODE_SPACE_PATH` 指向 workspace 根目錄（而非 codespace/ 子目錄）
- 不影響已存在的 bora/ 資料夾與 .repo

---

### US-03：切換 Expert（換專家）

**背景**：同仁完成編譯後，想換 cicd-expert 來處理 CI/CD 流程。

**流程**：
```
1. 執行 source experts/cicd-expert/install.sh --switch
2. 系統先觸發 hand-off，儲存當前 session 狀態
3. 移除舊 Expert 的所有 symlinks
4. 建立新 Expert 的 symlinks（common + private）
5. 重新生成 CLAUDE.md 與 expert.md
6. 印出變更清單：
   ✓ 新增: pipeline-operations, ci-patterns
   ✗ 移除: build-systems
   ○ 保留: expert-discovery, handoff-protocol（common，不變）
7. 同仁確認後，開啟 Claude Code 進入新 Expert 環境
```

**為什麼需要列出清單**：讓同仁清楚知道能力邊界已改變，避免誤以為仍有前一個 Expert 的技能。

---

### US-04：後臺資料收集

**背景**：主管想了解同仁使用哪些 Expert 最多、哪些 Hand-off 流程最常卡關。

**流程**：
```
1. session-end hook 在每次對話結束時自動觸發
2. 將 session 摘要寫入 consys-memory/employees/{username}/sessions/YYYY-MM-DD.md
3. 自動 git push 到 consys-memory 的 remote（同一個 repo，不同資料夾）
4. 管理者可 clone consys-memory，查看所有同仁的使用資料
5. 同仁也可手動執行 /handoff 在切換 Expert 時保存上下文
```

**為什麼用 Git 而非資料庫**：不需要額外基礎設施，每個人都懂 git，資料天然有版本歷史，且可在本地端離線使用。

---

## 3. 系統邊界與目錄結構

### 3.1 `consys-harness-experts` Repo 結構

```
consys-harness-experts/ (git)
├── README.md
├── registry.json                    ← 所有 Expert 目錄（expert-discovery 用）
├── install.sh                       ← 頂層：設定環境變數、clone consys-memory
│
├── common/                          ← 所有 Expert 共用（切換時整體替換）
│   ├── skills/
│   │   ├── expert-discovery/
│   │   │   └── SKILL.md             ← 有哪些專家？各自能做什麼？
│   │   └── handoff-protocol/
│   │       └── SKILL.md
│   ├── hooks/                       ← 實作方式 TBD（JS/TS/Python/shell）
│   │   ├── session-start.js
│   │   ├── session-end.js           ← 結束時儲存記憶 + push consys-memory
│   │   ├── pre-compact.js
│   │   ├── mid-session-checkpoint.js
│   │   └── shared-utils.js
│   └── commands/
│       ├── experts.md               ← /experts：列出所有 Expert + 說明切換方式
│       └── handoff.md               ← /handoff：手動觸發 hand-off
│
├── experts/
│   ├── build-expert/
│   │   ├── expert.json              ← 名稱/描述/觸發詞/skills/transitions/dependencies
│   │   ├── CLAUDE.md                ← @include .claude/expert.md
│   │   │                               @include .claude/expert.local.md
│   │   ├── install.sh               ← 此 Expert 的安裝腳本
│   │   └── skills/
│   │       └── build-systems/
│   │           └── SKILL.md
│   ├── cicd-expert/
│   │   ├── expert.json
│   │   ├── CLAUDE.md
│   │   ├── install.sh
│   │   └── skills/
│   │       └── pipeline-operations/
│   │           └── SKILL.md
│   └── device-expert/
│       ├── expert.json
│       ├── CLAUDE.md
│       ├── install.sh
│       └── skills/
│           └── device-control/
│               └── SKILL.md
│
└── external/                        ← 社群優質工具（以工具名稱為資料夾名）
    ├── skill-creator/               ← 快速建立/優化 Skill 的工具
    │   └── (原始 repo 結構)
    ├── claude-memory-engine/        ← 參考實作：8-step 學習循環記憶引擎
    │   ├── hooks/
    │   ├── commands/
    │   └── skill/
    └── {other-tool}/
        └── (原始 repo 結構)
```

**external/ 的設計理由**：
- 以工具名稱為資料夾，直接看出來源，避免混淆
- 可用 git submodule 管理，追蹤原始 repo 版本
- install.sh 透過 registry.json 知道要從 external/ 中的哪個工具連結哪些 skills/commands/hooks

---

### 3.2 Agent First 場景：workspace 演進

**Step 0 — 初始狀態（空 workspace）**
```
workspace/
└── （空）
```

**Step 1 — clone consys-harness-experts**
```
workspace/
└── consys-harness-experts/ (git)
```

**Step 2 — `source consys-harness-experts/experts/build-expert/install.sh`**
```
workspace/
├── consys-harness-experts/ (git)
│
├── consys-memory/ (git)                         ← install.sh 自動 clone
│   └── employees/
│       └── john.doe/                            ← git config user.name 自動取得
│           ├── sessions/
│           ├── handoffs/
│           └── summary.md
│
├── CLAUDE.md                                    ← 生成（非 symlink）
│   # @.claude/expert.md
│   # @.claude/expert.local.md
│
└── .claude/
    ├── expert.md                                ← 由 expert.json 生成，描述此 Expert 能力
    ├── expert.local.md                          ← 使用者客製化（選填，不在 repo 中）
    ├── .active-expert                           ← 內容："build-expert"
    ├── skills/
    │   ├── expert-discovery → $CONSYS_EXPERTS_PATH/common/skills/expert-discovery/
    │   ├── handoff-protocol → $CONSYS_EXPERTS_PATH/common/skills/handoff-protocol/
    │   └── build-systems    → $CONSYS_EXPERTS_PATH/experts/build-expert/skills/build-systems/
    ├── hooks/                                   ← symlinks，由 setup-claude.sh 在 settings.json 啟用
    │   ├── session-start.js          → $CONSYS_EXPERTS_PATH/common/hooks/session-start.js
    │   ├── session-end.js            → $CONSYS_EXPERTS_PATH/common/hooks/session-end.js
    │   ├── pre-compact.js            → $CONSYS_EXPERTS_PATH/common/hooks/pre-compact.js
    │   ├── mid-session-checkpoint.js → $CONSYS_EXPERTS_PATH/common/hooks/mid-session-checkpoint.js
    │   └── shared-utils.js           → $CONSYS_EXPERTS_PATH/common/hooks/shared-utils.js
    └── commands/
        ├── experts.md  → $CONSYS_EXPERTS_PATH/common/commands/experts.md
        └── handoff.md  → $CONSYS_EXPERTS_PATH/common/commands/handoff.md
```

**Step 3 — 使用者開啟 Claude Code，與 build-expert 互動，下載 fw**
```
workspace/
├── consys-harness-experts/ (git)
├── consys-memory/ (git)
├── CLAUDE.md
├── .claude/ (同上)
│
└── codespace/                                   ← $CONSYS_CODE_SPACE_PATH
    └── fw/                                      ← 第一套 firmware（repo tool 下載）
        ├── .repo (git)
        └── bora/
            ├── bt/ (git)
            ├── build/ (git)
            ├── wifi/ (git)
            └── mcu/ (git)
```

**Step 4 — 下載第二套 fw + driver SDK（可能有上百個 repo）**
```
workspace/
├── consys-harness-experts/ (git)
├── consys-memory/ (git)
├── CLAUDE.md
├── .claude/
└── codespace/
    ├── fw/ (同 Step 3)
    ├── fw2/                                     ← 第二套 firmware
    │   ├── .repo (git)
    │   └── bora/
    │       ├── bt/ (git)
    │       ├── build/ (git)
    │       ├── mcu/ (git)
    │       └── wifi/ (git)
    ├── drv/                                     ← gen4m driver SDK（可能上百個 repo）
    │   ├── .repo (git)
    │   └── gen4m/
    │       ├── wlan_gen4m/ (git)
    │       └── wlan_private/ (git)
    └── drv2/                                    ← logan driver SDK
        ├── .repo (git)
        └── logan/
            ├── wlan_logan/ (git)
            └── wlan_hwifi/ (git)
```

---

### 3.3 Legacy 場景：workspace 演進

**Step 0 — 初始狀態（傳統 repo tool 流程）**
```
workspace/
├── .repo (git)
└── bora/
    ├── wifi/ (git)
    ├── bt/ (git)
    ├── mcu/ (git)
    ├── build/ (git)
    └── coexistence/ (git)
```

**Step 1 — clone consys-harness-experts**
```
workspace/
├── .repo (git)
├── bora/ (同上)
└── consys-harness-experts/ (git)
```

**Step 2 — `source consys-harness-experts/experts/build-expert/install.sh`**
（install.sh 自動偵測到根目錄有 `.repo`，判斷為 legacy 場景）
```
workspace/
├── .repo (git)
├── bora/
│   ├── wifi/ (git)
│   ├── bt/ (git)
│   ├── mcu/ (git)
│   ├── build/ (git)
│   └── coexistence/ (git)
│
├── consys-harness-experts/ (git)
│
├── consys-memory/ (git)
│   └── employees/
│       └── john.doe/
│           ├── sessions/
│           ├── handoffs/
│           └── summary.md
│
├── CLAUDE.md                                    ← 生成
│
└── .claude/
    ├── expert.md
    ├── expert.local.md                          ← 選填
    ├── .active-expert                           ← "build-expert"
    ├── skills/
    │   ├── expert-discovery → $CONSYS_EXPERTS_PATH/common/skills/expert-discovery/
    │   ├── handoff-protocol → $CONSYS_EXPERTS_PATH/common/skills/handoff-protocol/
    │   └── build-systems    → $CONSYS_EXPERTS_PATH/experts/build-expert/skills/build-systems/
    ├── hooks/
    │   ├── session-start.js          → $CONSYS_EXPERTS_PATH/common/hooks/session-start.js
    │   ├── session-end.js            → $CONSYS_EXPERTS_PATH/common/hooks/session-end.js
    │   ├── pre-compact.js            → $CONSYS_EXPERTS_PATH/common/hooks/pre-compact.js
    │   ├── mid-session-checkpoint.js → $CONSYS_EXPERTS_PATH/common/hooks/mid-session-checkpoint.js
    │   └── shared-utils.js           → $CONSYS_EXPERTS_PATH/common/hooks/shared-utils.js
    └── commands/
        ├── experts.md  → $CONSYS_EXPERTS_PATH/common/commands/experts.md
        └── handoff.md  → $CONSYS_EXPERTS_PATH/common/commands/handoff.md
```

**兩個場景的主要差異**：

| | Agent First | Legacy |
|---|---|---|
| source code 位置 | `workspace/codespace/` | `workspace/`（已存在） |
| `CONSYS_CODE_SPACE_PATH` | `~/workspace/codespace` | `~/workspace` |
| code 由誰下載 | Claude 互動後用 repo tool 下載 | 同仁已手動下載 |
| 場景自動偵測 | 根目錄無 `.repo` | 根目錄有 `.repo` |

---

## 4. 功能需求

### FR-01：Expert Repo 結構

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-01-1 | repo 命名為 `consys-harness-experts`，Expert 資料夾命名為 `experts/` | Must | 避免與 AI 的「agent」概念混淆，名稱更 general |
| FR-01-2 | 每個 Expert 資料夾含 `expert.json`、`CLAUDE.md`、`install.sh`、`skills/` | Must | 標準化結構，讓 install.sh 可一致處理 |
| FR-01-3 | `expert.json` 含名稱、描述、觸發詞、skills 清單、transitions、dependencies | Must | 資訊越完整，expert-discovery 技能越有用 |
| FR-01-4 | `common/` 存放所有 Expert 共用的 skills/hooks/commands | Must | 避免重複定義，切換 Expert 時 common 部分一起替換 |
| FR-01-5 | `external/` 存放社群工具，以工具名稱為資料夾名（git submodule） | Should | 整合優質社群工具，避免重造輪子，submodule 管理版本 |
| FR-01-6 | `registry.json` 列出所有 Expert 及其 metadata | Must | expert-discovery 技能的資料來源 |

### FR-02：install.sh

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-02-1 | 支援 `--copy` 參數，預設為 symlink 模式 | Must | symlink 是切換 Expert 的基礎；copy 模式保留以應對特殊環境 |
| FR-02-2 | 支援 `--uninstall` 參數，移除當前 Expert 的所有 links | Must | 切換 Expert 時需要先 uninstall |
| FR-02-3 | 支援 `--switch` 參數（= uninstall 舊的 + install 新的 + 印出 diff） | Must | 提升切換體驗，讓同仁看清楚技能組合的變化 |
| FR-02-4 | 支援 `--target openclaw` 參數（未來） | Should | 為 OpenClaw 遷移預留入口，降低未來移植成本 |
| FR-02-5 | 支援 `--scenario [agent-first\|legacy]` 參數，預設自動偵測 | Must | 兩個場景的 codespace 路徑不同 |
| FR-02-6 | 支援 `--env-only` 參數，僅設定環境變數 | Should | 解決環境變數問題時不需重跑全部安裝流程 |
| FR-02-7 | install.sh **不**修改 `settings.json` / `settings.local.json` | Must | 平台設定由 `setup-claude.sh` 處理，解耦平台相依性 |
| FR-02-8 | install.sh **不**包含 MCP 設定 | Must | MCP 無法用 symlink 實作，屬不同層次的設定 |
| FR-02-9 | install.sh 以 `source` 方式執行，設定環境變數到當前 shell | Must | `./install.sh` 無法把環境變數帶回 parent shell |
| FR-02-10 | 首次執行時自動 clone `consys-memory` repo | Must | 後臺資料收集的基礎設施 |
| FR-02-11 | 切換 Expert 時印出變更清單（新增/移除/保留的 skills） | Must | 讓同仁知道能力邊界已改變 |
| FR-02-12 | 實作方式保留彈性（shell/npx/Python/TypeScript） | Must | 不同環境的可用工具不同，避免強依賴 |

### FR-03：環境變數

| 編號 | 需求 | 優先級 |
|------|------|--------|
| FR-03-1 | `CONSYS_EXPERTS_PATH`：指向 `consys-harness-experts` repo 路徑 | Must |
| FR-03-2 | `CONSYS_CODE_SPACE_PATH`：指向 codespace 目錄（agent-first: `codespace/`; legacy: workspace 根目錄） | Must |
| FR-03-3 | `CONSYS_MEMORY_PATH`：指向 `consys-memory` repo 路徑 | Must |
| FR-03-4 | `CONSYS_EMPLOYEE_ID`：自動從 `git config user.name` 取得 | Must |

### FR-04：Skill 系統

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-04-1 | 每個 Skill 以獨立資料夾存放，含 `SKILL.md`（YAML frontmatter + 內容） | Must | 結構化格式，未來遷移至 OpenClaw 直接相容 |
| FR-04-2 | `expert-discovery` skill 列出所有 Expert 及其能力，讓 Claude 可回答「有哪些專家」 | Must | 基本的系統可發現性 |
| FR-04-3 | `handoff-protocol` skill 定義交接格式與流程 | Must | 所有 Expert 都需要知道如何交接 |
| FR-04-4 | Expert 可有私有 skills，切換時一併替換 | Must | 不同專家有不同的專業知識庫 |
| FR-04-5 | External skills 透過 registry 聲明，install.sh 自動建立 link | Should | 整合社群工具 |

### FR-05：CLAUDE.md 生成機制

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-05-1 | install.sh 在 workspace 根目錄生成 `CLAUDE.md`（非 symlink） | Must | CLAUDE.md @include 的相對路徑需從根目錄計算 |
| FR-05-2 | CLAUDE.md @include `.claude/expert.md`（由 expert.json 生成）| Must | 將結構化 JSON 轉成 Claude 可讀的 Markdown |
| FR-05-3 | CLAUDE.md @include `.claude/expert.local.md`（若存在） | Must | 允許個人客製化，不污染 repo |
| FR-05-4 | `expert.local.md` 不納入 `consys-harness-experts` repo，以 `.gitignore` 排除 | Must | 個人設定不應影響其他同仁 |
| FR-05-5 | `expert.md` 中說明 `expert.local.md` 的存在與用途 | Should | 讓同仁知道有客製化入口 |

### FR-06：記憶系統

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-06-1 | 本地記憶以 Markdown 為格式 | Must | 透明可編輯，無外部依賴 |
| FR-06-2 | `session-end` hook 在對話結束時自動儲存 session 摘要 | Must | 確保記憶不遺失 |
| FR-06-3 | `pre-compact` hook 在 context 壓縮前儲存快照（最可靠的存檔點） | Must | 參考 claude-memory-engine 的三存檔點設計 |
| FR-06-4 | `mid-session-checkpoint` hook 每 20 訊息存一次 | Should | 避免長 session 中途資料遺失 |
| FR-06-5 | `session-start` hook 載入上次摘要 + 偵測待接 hand-off | Must | 新 session 能延續上次工作 |
| FR-06-6 | 記憶資料自動 push 到 `consys-memory` repo（可設定手動/自動）| Must | 後臺收集與跨裝置同步的基礎 |

### FR-07：Hand-off 協議

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-07-1 | Hand-off 發生時機：切換 Expert 時（--switch）、session 結束時 | Must | 確保上下文不遺失 |
| FR-07-2 | Hand-off 文件格式：YAML frontmatter（含 from/to/status/run-id）+ Markdown 摘要 | Must | 結構化格式，未來可程式化解析 |
| FR-07-3 | Hand-off 摘要控制在 2000 tokens 以內 | Must | 避免下一個 Expert 開始時就 context 爆炸 |
| FR-07-4 | 提供 `/handoff` 指令供同仁手動觸發 | Must | 手動觸發的需求真實存在 |
| FR-07-5 | Hand-off 文件存入 `consys-memory/employees/{id}/handoffs/` | Must | 後臺資料收集的一部分 |

### FR-08：後臺資料收集

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-08-1 | `consys-memory` 為單一 repo，所有同仁 push 到同一個 remote，以工號（git username）為子資料夾 | Must | 集中管理，不需每人維護自己的 repo |
| FR-08-2 | 收集內容：session 摘要、hand-off 文件、使用的 Expert 名稱 | Must | 管理者可分析哪些 Expert 最常用、哪些流程最常卡關 |
| FR-08-3 | 預設自動 push，可設定為手動 | Must | 減少同仁操作負擔；保留手動選項應對網路受限環境 |
| FR-08-4 | 同仁可用 `/handoff` 手動觸發 push | Must | 主動上傳的需求真實存在 |

### FR-09：Expert 設定檔（expert.json）

```json
{
  "name": "build-expert",
  "display_name": "Build Expert",
  "description": "專門處理韌體編譯、建置系統設定與編譯錯誤排查",
  "version": "1.0.0",
  "triggers": ["build", "compile", "編譯", "BUILD_FAILED"],
  "transitions": {
    "BUILD_SUCCESS": "cicd-expert",
    "BUILD_FAILED": null
  },
  "shared_skills": ["expert-discovery", "handoff-protocol"],
  "private_skills": ["build-systems"],
  "shared_commands": ["experts", "handoff"],
  "shared_hooks": ["session-start", "session-end", "pre-compact", "mid-session-checkpoint"],
  "external_tools": [],
  "scenarios": ["agent-first", "legacy"],
  "dependencies": []
}
```

---

## 5. 非功能需求

| 類別 | 需求 | 理由 |
|------|------|------|
| **可遷移性** | Skill 格式相容 OpenClaw SKILL.md 規範；Hook 以 JS 實作，未來改為 TypeScript handler.ts 成本低 | 不綁定特定平台是核心設計目標 |
| **可擴充性** | 新增 Expert 只需新增資料夾 + expert.json + install.sh，不修改其他 Expert | 降低同仁貢獻新 Expert 的門檻 |
| **可稽核性** | Hand-off 與 session 記憶均透過 Git 保存，支援 diff 與歷史查詢 | 後臺分析與問題溯源的基礎 |
| **Context 效率** | Hand-off 摘要 < 2000 tokens | 避免新 Expert 開始時就面臨 context 爆炸 |
| **相容性** | 完全運行於 Claude Code CLI，不依賴外部服務或資料庫 | 降低部署複雜度 |
| **透明性** | 所有 hooks 以可讀的 JS/TS/shell 實作，同仁可自行檢視與修改 | 參考 claude-memory-engine 的設計哲學：no black boxes |

---

## 6. 限制與假設

### 限制

- 本期 install.sh 僅處理 symlink/copy，不觸碰 `settings.json`（由 `setup-claude.sh` 處理）
- MCP 設定不在 install.sh 範圍內（無法用 link 實作）
- Symlink 在 Windows 環境需要額外處理（本期不支援）
- `consys-memory` repo 的 push 需要同仁對 remote 有寫入權限

### 假設

- 同仁具備基本終端機操作能力
- 執行環境已安裝 Claude Code CLI、Git、bash
- 同仁的 git config user.name 即其工號（企業環境統一設定）
- `consys-memory` remote 由管理者預先建立並開放所有同仁寫入

---

## 7. 遷移路線

```
Phase 1：Claude Code（現在）
  install.sh symlink → .claude/skills, hooks, commands
  CLAUDE.md 生成機制
  consys-memory Git 後臺

Phase 2：OpenClaw
  install.sh --target openclaw
  SKILL.md 直接相容
  bash hooks → TypeScript handler.ts
  consys-memory → workspace/MEMORY.md + LanceDB

Phase 3：ADK/SDK
  expert.json → AgentDefinition
  手動 install → 自動安裝
  Markdown hand-off → JSON output_format
```

---

## 8. 名詞定義

| 術語 | 定義 |
|------|------|
| Expert | 針對特定任務的 AI 專家設定（取代「Agent」，避免與 AI agent 概念混淆） |
| consys-harness-experts | 團隊共同維護的 Expert 工具 repo，包含所有 Expert 的 skills/hooks/commands |
| consys-memory | 後臺資料收集 repo，以員工工號（git username）為子資料夾 |
| install.sh | 安裝腳本，建立 symlinks，生成 CLAUDE.md，設定環境變數 |
| Agent First | 從空白 workspace 開始，由 Expert 引導下載 code 的使用場景 |
| Legacy | 同仁已手動下載 code，後續引入 Expert 的使用場景 |
| codespace | Agent First 場景下，Expert 引導下載的 source code 集中目錄 |
| Hand-off | Expert 切換或 session 結束時產生的結構化上下文摘要文件 |
| common/ | 所有 Expert 共用的 skills/hooks/commands，切換時整體替換 |
| external/ | 整合的社群優質工具，以工具名稱為資料夾名 |
| expert.md | 由 install.sh 從 expert.json 生成的可讀 Markdown，Claude 透過此文件理解當前 Expert 的能力 |
| expert.local.md | 使用者個人客製化檔，不納入 consys-harness-experts repo |
| CONSYS_EXPERTS_PATH | 指向 consys-harness-experts repo 的環境變數 |
| CONSYS_CODE_SPACE_PATH | 指向 source code 目錄的環境變數（兩個場景值不同） |
