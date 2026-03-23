# Consys Experts — 需求書

**文件版本**：v2.4
**狀態**：Draft
**目標讀者**：架構師、開發者、產品負責人
**改版說明**：
- v2.0：以使用者故事為主軸重寫，記錄設計決策的「為什麼」
- v2.1：明確 Expert 定義、引入 Harness Engineering 概念、repo 更名為 `consys-experts`、補充環境變數定義
- v2.2：expert.json 加入 owner、環境變數統一 CONSYS_EXPERTS_ 前綴、Agent First 流程補充 clone 步驟、skill 名稱更新
- v2.3：新增 Future Work（Security / Memory+Learn）、參考資料
- v2.4：加入三階段演進願景、Expert 交接流程需求、本地三區記憶設計需求

> **注意**：文件中所列的 expert、skill 名稱均為**示例**，用於說明命名規則與架構設計。實際規劃以團隊討論為準。

---

## 1. 背景與目標

### 1.1 啟發：Harness Engineering

> 參考來源：[Exploring Gen AI — Harness Engineering](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html)
> 作者：Birgitta Böckeler（Thoughtworks 傑出工程師），發表於 Martin Fowler 部落格

**Harness Engineering** 是一個新興工程概念：不再只是對 AI 下指令（Prompting），而是建立一套**環繞在 AI 模型周圍的系統、工具與實踐**，用以約束、引導並強化 AI Agent 的能力。

文章提出三大關鍵組件：

| 組件 | 定義 | 對應本系統的設計 |
|------|------|-----------------|
| **上下文工程**（Context Engineering） | 持續維護知識庫，讓 Agent 能存取動態資料 | SKILL.md 技能庫、expert.md、expert.local.md |
| **架構約束**（Architectural Constraints） | 加入確定性工具（Linter、測試），強制執行規範 | Hooks（pre-compact、write-guard）、hand-off 格式規範 |
| **垃圾回收**（Garbage Collection） | 定期執行 Agent 清理過時文件，對抗系統熵增 | session-end 自動整理記憶，push 至 consys-memory |

**文章關鍵結論**：隨著 AI Agent 的進化，軟體開發的嚴謹性（Rigor）正從「代碼細節」遷移到「系統架構與環境設計」。工程師的工作重點將從「打字寫代碼」轉向**「設計環境、反饋循環與控制系統」**。

本系統正是基於 Harness Engineering 的精神，為 Consys 韌體開發團隊打造的 AI Expert Harness。

---

### 1.2 Consys Expert 的定義

**Consys Expert = Agent 能力 + Consys Workflow + Consys Tool + Consys Knowledge**

```
┌─────────────────────────────────────────────────────────────┐
│                      Consys Expert                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Agent 核心能力（平台提供）               │   │
│  │         Think → Plan → Act → Learn（循環）           │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↑ 加上                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Workflow   │  │     Tool     │  │    Knowledge     │  │
│  │（工作流程）   │  │  （工具）    │  │    （知識）       │  │
│  │              │  │              │  │                  │  │
│  │ common/      │  │ common/      │  │ common/          │  │
│  │ experts/{n}/ │  │ experts/{n}/ │  │ experts/{n}/     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

每個 Expert 可以：
- 使用 **common** Workflow / Tool / Knowledge（所有 Expert 共用）
- 擁有自己的**私有** Workflow / Tool / Knowledge
- 在 install.sh 中透過 link 或 copy 將上述內容接入 Claude Code（或未來的其他 Agent 平台）

**開發範圍不限於韌體**，包含但不限於：
- Firmware（韌體）
- Driver（驅動程式）
- User Space 應用程式
- 自動化工具（如 FW Parser、Python 工具、CI/CD 腳本）

---

### 1.3 問題陳述

韌體開發團隊的日常工作涉及多個 repo 的下載、編譯、修復、上傳與裝置控制。目前工作流程完全依賴人工判斷，導致以下痛點：

- 每位同仁對工具鏈的熟悉程度不同，重複踩坑
- AI 輔助工具（Claude Code）的使用方式因人而異，效益不一致
- Agent 與 Agent 之間的上下文無法有效傳遞（Context 爆炸問題）
- 無法收集使用資料，難以知道哪些流程需要改善

### 1.4 目標

建立一套以 **Claude Code** 為執行環境、可跨平台遷移的 **Consys Expert Harness**，達成：

1. 同仁可快速安裝對應領域的「專家」(Expert)，取得即用的 Skills（Knowledge）、Hooks（Workflow）與 Commands（Tool）
2. Expert 之間透過結構化 Hand-off 傳遞上下文，避免 Context 爆炸
3. 使用資料自動收集至後臺 Git repo，供反思與大數據分析
4. **未來目標**：Agent 可自行 install、自行運作；簡單任務由 Agent 自動完成，有風險時觸發 **Human in the Loop** 機制，請人類介入確認
5. 架構不綁定特定 AI 平台，未來可平滑遷移至 OpenClaw 或 ADK/SDK

---

### 1.5 三階段演進願景

本系統的設計以「逐步交還控制權給 Agent」為核心願景，共分三個階段演進：

```
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 1：Expert 需要人類輔助（Human-Assisted）                      │
│                                                                     │
│  Agent 協助人類完成任務，高風險操作需人類確認（Human in the Loop）。   │
│  Expert 之間的切換由人工執行（--switch）。                            │
│  這是本系統的 Phase 1 目標（現在）。                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Stage 2：部分 Expert 可獨立完成任務（Semi-Autonomous）               │
│                                                                     │
│  對於風險較低、流程明確的任務（如 build → CI），Expert 可自動執行       │
│  完整流程，包含自動切換到下一個 Expert（根據 transitions 設定）。       │
│  仍對高風險操作觸發 Human in the Loop。                              │
│  需要成熟的記憶系統支撐（Local Memory + consys-memory）。             │
├─────────────────────────────────────────────────────────────────────┤
│  Stage 3：Expert 之間可互相溝通（Multi-Agent Collaboration）          │
│                                                                     │
│  多個 Expert 可平行運作，透過結構化 Hand-off 與共享記憶互相協調。       │
│  例如 build-expert 發現問題後，主動通知 debug-expert 接手。            │
│  Expert 可透過 framework-memory-tool 讀寫共用記憶區。                │
│  這是本系統的長期目標，對應 ADK/SDK 的 Multi-Agent 架構。             │
└─────────────────────────────────────────────────────────────────────┘
```

**為什麼要定義三個階段**：
- 讓團隊對「現在做什麼」與「未來走向哪裡」有共識
- 記憶設計（本地三區）和交接流程設計，從 Stage 1 開始就要為 Stage 2/3 預留空間
- 每個階段的技術投資都有意義：記憶收集的資料，未來可用於 Stage 3 的 Expert 協調

---

### 1.6 設計決策的理由

| 設計決策 | 理由 |
|---------|------|
| Expert = Agent + Workflow + Tool + Knowledge | 讓 Claude Code 成為真正懂 Consys 流程的專家，而非通用 AI |
| 獨立的 `consys-experts` repo | Expert 工具與 source code 分開管理，兩者生命週期不同；同仁可在任何 workspace 安裝 |
| 以 symlink 為預設安裝方式 | 切換 Expert 時直接重建 link 即可，無需處理檔案複製的一致性問題 |
| CLAUDE.md 採覆蓋（替換）策略 | 切換 Expert 等於「換一個專家來做事」——新專家帶來全新的技能組合 |
| install.sh 不觸碰 settings.json | 平台設定由 `setup-claude.sh` 處理，降低 install.sh 與平台的耦合 |
| 記憶系統用 Markdown + Git | 不需外部資料庫，完全透明可編輯，天然支援跨裝置同步與版本稽核 |
| 工號（git username）作為後臺資料夾名稱 | 無需額外帳號系統，git 帳號即工號，install.sh 可自動取得 |
| `external/` 資料夾 | 避免重造輪子，整合社群優秀工具（如 skill-creator），以工具名稱為資料夾名 |
| Human in the Loop 設計 | 對於有風險的操作（刪除、push、裝置控制），Agent 應先警告並等待人類確認，避免不可逆的錯誤 |

---

## 2. 使用者故事

### US-01：Agent First 場景（從空白 workspace 開始）

**背景**：同仁拿到一台新機器，workspace 是空的，想用 Expert 輔助下載並編譯韌體。

**流程**：
```
0. 初始狀態：~/workspace/ 為空目錄
1. 在 ~/workspace/ 執行：git clone {consys-experts-url}
   → 出現 ~/workspace/consys-experts/
2. 瀏覽 consys-experts/ 資料夾，找到所需 Expert（如 wifi/experts/wifi-build-expert/）
3. 執行：source consys-experts/wifi/experts/wifi-build-expert/install.sh
   → 建立 .claude/ symlinks、生成 CLAUDE.md、設定環境變數
4. 開啟 Claude Code → 已具備 wifi-build-expert 的 Skills/Hooks/Commands
5. 與 Claude 互動，Claude 協助用 repo tool 下載 fw 到 codespace/fw/
6. 需要切換到 wifi-cicd-expert 時：
   source consys-experts/wifi/experts/wifi-cicd-expert/install.sh --switch
   確認變更清單後，重新開啟 Claude Code
```

**驗收條件**：
- install.sh 執行後，`.claude/skills/`、`.claude/hooks/`、`.claude/commands/` 均正確建立 symlink
- `CLAUDE.md` 被生成，內容 @include `expert.md` 與 `expert.local.md`
- 環境變數正確設定（見 FR-03）
- `consys-memory/` repo 被自動 clone，員工資料夾以 git username 命名

---

### US-02：Legacy 場景（已手動下載 code）

**背景**：同仁已用 `repo` 工具按照傳統流程下載好 fw，現在想引入 Expert 輔助。

**流程**：
```
1. 同仁已有：
   ~/workspace/.repo
   ~/workspace/bora/wifi, bt, mcu, build, coexistence (各為獨立 git repo)
2. 在 ~/workspace/ clone consys-experts
3. 執行 source experts/build-expert/install.sh
4. install.sh 自動偵測到 .repo 存在，判斷為 legacy 場景
5. 建立 .claude/ symlinks，生成 CLAUDE.md
6. 開啟 Claude Code，既有 code 與新安裝的 Expert 技能整合運作
```

**驗收條件**：
- install.sh 能自動偵測場景（legacy vs agent-first）
- Legacy 場景的 `CONSYS_EXPERTS_CODE_SPACE_PATH` 指向 workspace 根目錄
- 不影響已存在的 bora/ 資料夾與 .repo

---

### US-03：切換 Expert（換專家）

**背景**：同仁完成編譯後，想換 cicd-expert 來處理 CI/CD 流程。

**流程**：
```
1. 執行 source experts/cicd-expert/install.sh --switch
2. 系統先觸發 hand-off，儲存當前 session 狀態
3. 移除舊 Expert 的所有 symlinks（common + private 全部替換）
4. 建立新 Expert 的 symlinks
5. 重新生成 CLAUDE.md 與 expert.md
6. 印出變更清單：
   ✓ 新增: pipeline-operations, ci-patterns
   ✗ 移除: build-systems
   ○ 保留: expert-discovery, handoff-protocol（common，不變）
7. 同仁確認後，開啟 Claude Code 進入新 Expert 環境
```

**為什麼 common 也要替換**：切換 Expert 等於「換一個專家」，新專家帶來整套技能組合。即使 common skills 內容相同，link 也應重建以確保一致性，並讓使用者看到完整的切換清單。

---

### US-04：Agent 自動運作（未來目標）

**背景**：Agent 自行判斷任務，自動完成簡單操作，遇到風險時觸發 Human in the Loop。

**流程**：
```
1. Agent 收到任務：「幫我 build fw 並上傳到 CI」
2. Agent 自動執行：clone code → build → 分析結果
3. 遇到需要 push 到 remote 的步驟：
   ⚠️  警告：即將執行 git push origin main，此操作不可逆
   請確認後繼續 [y/N]：
4. 同仁確認 → Agent 繼續執行
5. Agent 自行 install 下一個需要的 Expert（未來）
```

---

### US-05：後臺資料收集與分析

**背景**：主管想了解同仁使用哪些 Expert 最多、哪些 Hand-off 流程最常卡關。

**流程**：
```
1. session-end hook 在每次對話結束時自動觸發
2. 將 session 摘要寫入 consys-memory/employees/{username}/sessions/YYYY-MM-DD.md
3. 自動 git push 到 consys-memory 的 remote
4. 管理者可 clone consys-memory，查看所有同仁的使用資料
5. 分析：哪些 Expert 最常用、哪些步驟最常需要人工介入
```

**為什麼用 Git**：不需要額外基礎設施，資料天然有版本歷史，可在本地端離線使用。

---

## 3. 系統邊界與目錄結構

### 3.1 `consys-experts` Repo 結構

```
consys-experts/ (git)
├── README.md
├── registry.json                    ← 所有 Expert 目錄（expert-discovery 用）
├── install.sh                       ← 頂層：設定環境變數、clone consys-memory
│
├── common/                          ← 所有 Expert 共用
│   ├── skills/                      ← Knowledge：共用知識庫
│   │   ├── expert-discovery/
│   │   │   └── SKILL.md             ← 有哪些專家？各自能做什麼？
│   │   └── handoff-protocol/
│   │       └── SKILL.md
│   ├── hooks/                       ← Workflow：自動觸發的工作流程
│   │   │                              實作方式 TBD（JS/TS/Python/shell）
│   │   ├── session-start.js         ← 載入上次摘要 + 偵測 hand-off
│   │   ├── session-end.js           ← 儲存記憶 + push consys-memory
│   │   ├── pre-compact.js           ← context 壓縮前存快照
│   │   ├── mid-session-checkpoint.js← 每 20 訊息自動存檔
│   │   └── shared-utils.js
│   └── commands/                    ← Tool：同仁可手動執行的指令
│       ├── experts.md               ← /experts：列出所有 Expert + 切換方式
│       └── handoff.md               ← /handoff：手動觸發 hand-off
│
├── experts/
│   ├── build-expert/                ← 懂編譯的專家
│   │   ├── expert.json
│   │   ├── CLAUDE.md
│   │   ├── install.sh
│   │   └── skills/                  ← 私有 Knowledge
│   │       └── build-systems/SKILL.md
│   ├── cicd-expert/                 ← 懂 CI/CD 的專家
│   │   ├── expert.json
│   │   ├── CLAUDE.md
│   │   ├── install.sh
│   │   └── skills/
│   │       └── pipeline-operations/SKILL.md
│   └── device-expert/               ← 懂裝置控制的專家
│       ├── expert.json
│       ├── CLAUDE.md
│       ├── install.sh
│       └── skills/
│           └── device-control/SKILL.md
│
└── external/                        ← 社群優質工具（工具名稱為資料夾名）
    ├── skill-creator/               ← 快速建立/優化 Skill
    ├── claude-memory-engine/        ← 8-step 學習循環記憶引擎（參考實作）
    └── {other-tool}/
```

---

### 3.2 Agent First 場景：workspace 演進

**Step 0 — 初始狀態（空 workspace）**
```
workspace/
└── （空）
```

**Step 1 — clone consys-experts**
```
workspace/
└── consys-experts/ (git)
```

**Step 2 — `source consys-experts/experts/build-expert/install.sh`**
```
workspace/                                       ← $CONSYS_EXPERTS_WORKSPACE_ROOT_PATH
├── consys-experts/ (git)
│
├── consys-memory/ (git)                         ← install.sh 自動 clone
│   └── employees/
│       └── john.doe/                            ← git config user.name
│           ├── sessions/
│           ├── handoffs/
│           └── summary.md
│
├── CLAUDE.md                                    ← 生成（非 symlink）
│   # @.claude/expert.md
│   # @.claude/expert.local.md
│
└── .claude/
    ├── expert.md                                ← 由 expert.json 生成
    ├── expert.local.md                          ← 個人客製化（選填，.gitignore）
    ├── .active-expert                           ← "build-expert"
    ├── skills/                                  ← Knowledge symlinks
    │   ├── expert-discovery → $CONSYS_EXPERTS_PATH/common/skills/expert-discovery/
    │   ├── handoff-protocol → $CONSYS_EXPERTS_PATH/common/skills/handoff-protocol/
    │   └── build-systems    → $CONSYS_EXPERTS_PATH/experts/build-expert/skills/build-systems/
    ├── hooks/                                   ← Workflow symlinks
    │   ├── session-start.js          → $CONSYS_EXPERTS_PATH/common/hooks/session-start.js
    │   ├── session-end.js            → $CONSYS_EXPERTS_PATH/common/hooks/session-end.js
    │   ├── pre-compact.js            → $CONSYS_EXPERTS_PATH/common/hooks/pre-compact.js
    │   ├── mid-session-checkpoint.js → $CONSYS_EXPERTS_PATH/common/hooks/mid-session-checkpoint.js
    │   └── shared-utils.js           → $CONSYS_EXPERTS_PATH/common/hooks/shared-utils.js
    └── commands/                                ← Tool symlinks
        ├── experts.md  → $CONSYS_EXPERTS_PATH/common/commands/experts.md
        └── handoff.md  → $CONSYS_EXPERTS_PATH/common/commands/handoff.md
```

**Step 3 — 開啟 Claude Code，Expert 協助下載 fw**
```
workspace/                                       ← $CONSYS_EXPERTS_WORKSPACE_ROOT_PATH
├── consys-experts/ (git)
├── consys-memory/ (git)
├── CLAUDE.md
├── .claude/
└── codespace/                                   ← $CONSYS_EXPERTS_CODE_SPACE_PATH
    └── fw/
        ├── .repo (git)
        └── bora/
            ├── bt/ (git)
            ├── build/ (git)
            ├── wifi/ (git)
            └── mcu/ (git)
```

**Step 4 — 下載多套 fw + driver SDK**
```
workspace/
├── consys-experts/ (git)
├── consys-memory/ (git)
├── CLAUDE.md
├── .claude/
└── codespace/                                   ← $CONSYS_EXPERTS_CODE_SPACE_PATH
    ├── fw/                                      ← 第一套 firmware
    │   ├── .repo (git)
    │   └── bora/
    │       ├── bt/ (git)
    │       ├── build/ (git)
    │       ├── wifi/ (git)
    │       └── mcu/ (git)
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

**Step 1 — clone consys-experts**
```
workspace/
├── .repo (git)
├── bora/ (同上)
└── consys-experts/ (git)
```

**Step 2 — `source consys-experts/experts/build-expert/install.sh`**
（install.sh 偵測到根目錄有 `.repo`，自動判斷 legacy 場景）
```
workspace/                                       ← $CONSYS_EXPERTS_WORKSPACE_ROOT_PATH
│                                                   $CONSYS_EXPERTS_CODE_SPACE_PATH（同一路徑）
├── .repo (git)
├── bora/
│   ├── wifi/ (git)
│   ├── bt/ (git)
│   ├── mcu/ (git)
│   ├── build/ (git)
│   └── coexistence/ (git)
├── consys-experts/ (git)
├── consys-memory/ (git)
├── CLAUDE.md                                    ← 生成
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
| Workspace root | `~/workspace/` | `~/workspace/` |
| Code space | `~/workspace/codespace/` | `~/workspace/`（同 workspace root）|
| `CONSYS_EXPERTS_CODE_SPACE_PATH` | `~/workspace/codespace` | `~/workspace` |
| code 由誰下載 | Claude Expert 互動後用 repo tool 下載 | 同仁已手動下載 |
| 場景自動偵測 | 根目錄無 `.repo` | 根目錄有 `.repo` |

---

## 4. 功能需求

### FR-01：Expert Repo 結構

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-01-1 | repo 命名為 `consys-experts`，Expert 資料夾命名為 `experts/` | Must | 避免與 AI 的「agent」概念混淆，名稱更 general |
| FR-01-2 | 每個 Expert 資料夾含 `expert.json`、`CLAUDE.md`、`install.sh`、`skills/` | Must | 標準化結構，讓 install.sh 可一致處理 |
| FR-01-3 | `expert.json` 含名稱、描述、觸發詞、skills、transitions、dependencies | Must | 資訊越完整，expert-discovery 越有用 |
| FR-01-4 | `common/` 分為 skills（Knowledge）、hooks（Workflow）、commands（Tool）三層 | Must | 對應 Expert 定義的三個組件 |
| FR-01-5 | `external/` 存放社群工具，以工具名稱為資料夾名（git submodule） | Should | 整合優質社群工具，避免重造輪子 |
| FR-01-6 | `registry.json` 列出所有 Expert 及其 metadata | Must | expert-discovery 的資料來源 |

### FR-02：install.sh

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-02-1 | 支援 `--copy` 參數，預設為 symlink 模式 | Must | symlink 是切換 Expert 的基礎 |
| FR-02-2 | 支援 `--uninstall` 參數，移除當前 Expert 的所有 links | Must | 切換 Expert 時需要先 uninstall |
| FR-02-3 | 支援 `--switch` 參數（= uninstall + install + 印出 diff）| Must | 提升切換體驗，讓同仁看清楚技能組合的變化 |
| FR-02-4 | 支援 `--target openclaw` 參數（未來） | Should | 為 OpenClaw 遷移預留入口 |
| FR-02-5 | 支援 `--scenario [agent-first\|legacy]` 參數，預設自動偵測 | Must | 兩個場景的 code space 路徑不同 |
| FR-02-6 | 支援 `--env-only` 參數，僅設定環境變數 | Should | 環境問題排查時不需重跑全部流程 |
| FR-02-7 | install.sh **不**修改 `settings.json` / `settings.local.json` | Must | 平台設定由 `setup-claude.sh` 處理，解耦平台相依 |
| FR-02-8 | install.sh **不**包含 MCP 設定 | Must | MCP 無法用 symlink 實作，屬不同層次的設定 |
| FR-02-9 | 以 `source` 方式執行，環境變數可帶回 parent shell | Must | `./install.sh` 無法把環境變數帶回 parent shell |
| FR-02-10 | 首次執行時自動 clone `consys-memory` repo | Must | 後臺資料收集的基礎設施 |
| FR-02-11 | 切換 Expert 時印出變更清單（新增/移除/保留的 skills） | Must | 讓同仁知道能力邊界已改變 |
| FR-02-12 | 實作方式保留彈性（shell / npx / Python / TypeScript） | Must | 不同環境的可用工具不同，避免強依賴 |

### FR-03：環境變數

所有環境變數由 install.sh 透過 `source` 設定，可供 Expert 的 workflow、skill、tool 直接使用。
**所有變數統一使用 `CONSYS_EXPERTS_` 前綴**。

| 環境變數 | 說明 | Agent First 範例值 | Legacy 範例值 |
|---------|------|-------------------|--------------|
| `CONSYS_EXPERTS_PATH` | `consys-experts` repo 的路徑 | `~/workspace/consys-experts` | `~/workspace/consys-experts` |
| `CONSYS_EXPERTS_WORKSPACE_ROOT_PATH` | 工作根目錄（`.claude/` 所在）| `~/workspace` | `~/workspace` |
| `CONSYS_EXPERTS_CODE_SPACE_PATH` | 程式碼路徑（source code repo 所在）| `~/workspace/codespace` | `~/workspace` |
| `CONSYS_EXPERTS_MEMORY_PATH` | `consys-memory` repo 的路徑 | `~/workspace/consys-memory` | `~/workspace/consys-memory` |
| `CONSYS_EXPERTS_EMPLOYEE_ID` | 員工工號（自動從 `git config user.name` 取得）| `john.doe` | `john.doe` |

**使用範例**（在 skill 或 hook 中）：
```bash
# 在 skill 中引用 code space 路徑
BUILD_DIR="$CONSYS_EXPERTS_CODE_SPACE_PATH/fw/bora/build"

# 在 hook 中推送記憶
git -C "$CONSYS_EXPERTS_MEMORY_PATH" push origin main
```

### FR-04：Skill 系統（Knowledge）

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-04-1 | 每個 Skill 以獨立資料夾存放，含 `SKILL.md`（YAML frontmatter + 內容） | Must | 結構化格式，未來遷移 OpenClaw 直接相容 |
| FR-04-2 | `expert-discovery` skill 列出所有 Expert 及能力 | Must | 基本的系統可發現性 |
| FR-04-3 | `handoff-protocol` skill 定義交接格式與流程 | Must | 所有 Expert 都需要知道如何交接 |
| FR-04-4 | Expert 可有私有 skills，切換時一併替換 | Must | 不同專家有不同的知識庫 |
| FR-04-5 | External skills 透過 registry 聲明，install.sh 自動建立 link | Should | 整合社群工具 |

### FR-05：CLAUDE.md 生成機制

| 編號 | 需求 | 優先級 |
|------|------|--------|
| FR-05-1 | install.sh 在 workspace 根目錄生成 `CLAUDE.md`（非 symlink） | Must |
| FR-05-2 | CLAUDE.md @include `.claude/expert.md`（由 expert.json 生成） | Must |
| FR-05-3 | CLAUDE.md @include `.claude/expert.local.md`（若存在） | Must |
| FR-05-4 | `expert.local.md` 不納入 `consys-experts` repo，以 `.gitignore` 排除 | Must |
| FR-05-5 | `expert.md` 中說明 `expert.local.md` 的存在與用途 | Should |

### FR-06：記憶系統（Workflow + 後臺）

#### FR-06A：四個 Hook 存檔點

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-06-1 | 本地記憶以 Markdown 為格式 | Must | 透明可編輯，無外部依賴 |
| FR-06-2 | `session-end` hook 自動儲存 session 摘要 | Must | 確保記憶不遺失 |
| FR-06-3 | `pre-compact` hook 在 context 壓縮前存快照（最可靠存檔點）| Must | 參考 claude-memory-engine 的三存檔點設計 |
| FR-06-4 | `mid-session-checkpoint` hook 每 20 訊息存一次 | Should | 避免長 session 中途資料遺失 |
| FR-06-5 | `session-start` hook 載入上次摘要 + 偵測待接 hand-off | Must | 新 session 能延續上次工作 |
| FR-06-6 | 記憶資料自動 push 到 `consys-memory` repo | Must | 後臺收集與跨裝置同步 |

#### FR-06B：本地三區記憶（Local Three-Zone Memory）

本地記憶存放於 `workspace/.claude/memory/`，分三個用途不同的區域，與遠端 `consys-memory` 後臺各司其職：

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-06-7 | 建立 `memory/shared/` 區域（跨 Expert 共用知識） | Must | 儲存 project.md、conventions.md 等跨 Expert 都需要的知識，Expert 切換後仍可讀取 |
| FR-06-8 | 建立 `memory/working/{expert}/` 區域（當前 Expert 的飛行中狀態） | Must | 儲存 in-flight 的工作日誌、決策記錄，Expert 切換時由 hand-off hook 清除（或歸檔），避免記憶污染 |
| FR-06-9 | 建立 `memory/handoffs/{run-id}/` 區域（交接文件，寫入後唯讀） | Must | 壓縮摘要 < 2000 tokens，新 Expert 由 session-start hook 讀取，確保交接資訊完整傳遞 |
| FR-06-10 | `session-start` hook 自動偵測 `memory/handoffs/` 是否有待接的 hand-off 文件 | Must | 新 Expert 啟動時不需人工操作即可拿到上一個 Expert 的交接內容 |
| FR-06-11 | 週期性記憶整理（Periodic Collection）：每日或每週自動彙整本地記憶至 consys-memory | Should | 收集長期知識，供未來 framework-learn-expert 分析，但不造成即時系統負擔 |

### FR-07：Hand-off 協議與 Expert 狀態機

| 編號 | 需求 | 優先級 |
|------|------|--------|
| FR-07-1 | Hand-off 發生時機：切換 Expert 時（--switch）、session 結束時 | Must |
| FR-07-2 | Hand-off 文件格式：YAML frontmatter + Markdown 摘要（< 2000 tokens）| Must |
| FR-07-3 | 提供 `/handoff` 指令供同仁手動觸發 | Must |
| FR-07-4 | Hand-off 文件同時存入本地 `memory/handoffs/{run-id}/`（當前 Expert 讀取用）及 `consys-memory/employees/{id}/handoffs/`（遠端備份） | Must |
| FR-07-5 | `expert.json` 的 `transitions` 欄位定義 Expert 的狀態機轉移（事件 → 下一個 Expert） | Must |
| FR-07-6 | 轉移事件（如 BUILD_SUCCESS / BUILD_FAILED）由 Expert 在工作完成後主動發出，觸發 hand-off 流程 | Must |
| FR-07-7 | 若轉移目標為 `null`（如 BUILD_FAILED），表示需要人工介入，Expert 應提示同仁並等待 | Must |
| FR-07-8 | Stage 2 未來：符合條件的 transitions 可自動觸發 install.sh --switch，無需人工操作 | Future |

### FR-08：後臺資料收集

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-08-1 | `consys-memory` 為單一 repo，以工號（git username）為子資料夾 | Must | 集中管理，不需每人維護自己的 repo |
| FR-08-2 | 收集內容：session 摘要、hand-off 文件、使用的 Expert 名稱 | Must | 管理者可分析哪些 Expert 最常用、哪些流程最常卡關 |
| FR-08-3 | 預設自動 push，可設定為手動 | Must | 減少同仁操作負擔 |

### FR-09：Human in the Loop（未來）

| 編號 | 需求 | 優先級 | 理由 |
|------|------|--------|------|
| FR-09-1 | 對不可逆操作（git push、裝置控制、刪除）先輸出警告，等待人類確認 | Must | 避免 Agent 自動操作造成不可逆損害 |
| FR-09-2 | 警告訊息包含：操作說明、影響範圍、確認提示 | Must | 讓同仁有足夠資訊做判斷 |
| FR-09-3 | Expert 可設定哪些操作需要人類介入（per-expert 設定） | Should | 不同 Expert 的風險等級不同 |
| FR-09-4 | 未來支援 Agent 自行 install 所需 Expert | Could | 實現完全自動化的先決條件 |

---

## 5. 非功能需求

| 類別 | 需求 | 理由 |
|------|------|------|
| **可遷移性** | Skill 格式相容 OpenClaw；Hook 以 JS 實作，未來改為 TypeScript 成本低 | 不綁定特定平台是核心設計目標 |
| **可擴充性** | 新增 Expert 只需新增資料夾 + expert.json + install.sh，不修改其他 Expert | 降低同仁貢獻新 Expert 的門檻 |
| **可稽核性** | Hand-off 與 session 記憶均透過 Git 保存，支援 diff 與歷史查詢 | 後臺分析與問題溯源的基礎 |
| **Context 效率** | Hand-off 摘要 < 2000 tokens | 避免新 Expert 開始時就面臨 context 爆炸 |
| **相容性** | 完全運行於 Claude Code CLI，不依賴外部服務或資料庫 | 降低部署複雜度 |
| **透明性** | 所有 hooks 以可讀的 JS/TS/shell 實作，同仁可自行檢視與修改 | 參考 Harness Engineering 的精神：no black boxes |

---

## 6. 限制與假設

### 限制

- 本期 install.sh 僅處理 symlink/copy，不觸碰 `settings.json`（由 `setup-claude.sh` 處理）
- MCP 設定不在 install.sh 範圍內
- Symlink 在 Windows 環境需要額外處理（本期不支援）
- `consys-memory` repo 的 push 需要同仁對 remote 有寫入權限
- Human in the Loop 功能為未來規劃，本期以人工切換 Expert 為主

### 假設

- 同仁具備基本終端機操作能力
- 執行環境已安裝 Claude Code CLI、Git、bash
- 同仁的 git config user.name 即其工號（企業環境統一設定）
- `consys-memory` remote 由管理者預先建立並開放所有同仁寫入

---

## 7. 遷移路線

```
Phase 1：Claude Code（現在）
  install.sh symlink → .claude/skills（Knowledge）, hooks（Workflow）, commands（Tool）
  CLAUDE.md 生成機制
  consys-memory Git 後臺收集
  Human in the Loop：人工切換 Expert

Phase 2：OpenClaw
  install.sh --target openclaw
  SKILL.md 直接相容
  bash hooks → TypeScript handler.ts
  consys-memory → workspace/MEMORY.md + LanceDB
  Human in the Loop：Hook 觸發確認機制

Phase 3：ADK/SDK（全自動）
  expert.json → AgentDefinition
  手動 install → Agent 自行 install
  Markdown hand-off → JSON output_format
  Human in the Loop：風險評分自動決定介入等級
```

---

## 8. 名詞定義

| 術語 | 定義 |
|------|------|
| Consys Expert | Agent 能力 + Consys Workflow + Consys Tool + Consys Knowledge 的組合體 |
| Harness Engineering | 為 AI 打造「自動化治理體系」，透過限制行為邊界與豐富上下文，實現大規模自動化（來源：Birgitta Böckeler / Martin Fowler Blog）|
| consys-experts | 團隊共同維護的 Expert 工具 repo |
| consys-memory | 後臺資料收集 repo，以員工工號（git username）為子資料夾 |
| install.sh | 安裝腳本，建立 symlinks，生成 CLAUDE.md，設定環境變數 |
| Agent First | 從空白 workspace 開始，由 Expert 引導下載 code 的場景 |
| Legacy | 同仁已手動下載 code，後續引入 Expert 的場景 |
| codespace | Agent First 場景下，Expert 引導下載的 source code 集中目錄 |
| Hand-off | Expert 切換或 session 結束時產生的結構化上下文摘要文件 |
| common/ | 所有 Expert 共用的 skills/hooks/commands |
| external/ | 整合的社群優質工具，以工具名稱為資料夾名 |
| expert.md | 由 install.sh 從 expert.json 生成的可讀 Markdown |
| expert.local.md | 使用者個人客製化檔，不納入 consys-experts repo |
| Human in the Loop | 對高風險操作暫停等待人類確認的機制 |
| `CONSYS_EXPERTS_PATH` | 指向 consys-experts repo 的環境變數 |
| `CONSYS_EXPERTS_WORKSPACE_ROOT_PATH` | 工作根目錄（.claude/ 所在），兩個場景均為 workspace 根目錄 |
| `CONSYS_EXPERTS_CODE_SPACE_PATH` | 程式碼路徑（Agent First: codespace/；Legacy: workspace 根目錄）|
| `CONSYS_EXPERTS_MEMORY_PATH` | 指向 consys-memory repo 的環境變數 |
| `CONSYS_EXPERTS_EMPLOYEE_ID` | 員工工號，自動從 git config user.name 取得 |

---

## 9. Future Work

### FW-01：Security — Expert 安全審計機制

**背景**：

AI Agent 生態系統的安全威脅已有實際案例：
- 2026 年 1 月，主要 Agent 技能市場中 **12%（341/2,857）為惡意技能**
- CVSS 8.8 的 CVE 暴露了 **17,500+ 個面向網路的實例**
- Moltbook 漏洞跨 770,000 個 Agent 洩露了 **150 萬個 API token**

目前同仁在安裝 external-experts、連接 MCP 伺服器、設定 hooks 時，沒有任何自動化安全審計機制。

**需求**：

| 編號 | 需求 | 優先級 |
|------|------|--------|
| FW-01-1 | 建立 `framework-security-expert`，提供自動化安全審計能力 | Future |
| FW-01-2 | 提供 pre-install hook，在安裝 external-experts 前自動掃描 | Future |
| FW-01-3 | 靜態分析 SKILL.md / COMMAND.md，偵測 prompt injection 與資料外洩指令 | Future |
| FW-01-4 | 掃描 hooks（.js）是否有可疑網路呼叫或非預期檔案讀寫 | Future |
| FW-01-5 | 產生安全掃描報告，更新至 `report/execution-report.md` | Future |

**參考實作**：[AgentShield](https://github.com/affaan-m/agentshield)

---

### FW-02：Memory + Learn — 自我檢討的 Expert

**背景**：

目前 Expert 的 knowledge（SKILL.md）是靜態的，由人工撰寫與維護。隨著 consys-memory 累積越來越多的使用記錄，有機會讓 Expert 從記憶中自動學習，持續改善自己的 skills。

**設計方向**：
```
使用記憶（sessions/ + handoffs/）
    → framework-learn-expert 分析
    → 找出 pattern（常見錯誤、成功解法）
    → 自動產生/更新 SKILL.md
    → PR → 人工 review → merge → 所有人受益
```

**需求**：

| 編號 | 需求 | 優先級 |
|------|------|--------|
| FW-02-1 | `framework-learn-expert` 能定期分析 consys-memory 的 session 記錄 | Future |
| FW-02-2 | 從記憶中萃取重複出現的問題與解法，產生 knowhow skill 草稿 | Future |
| FW-02-3 | 自動建立 PR，由人工 review 後合入 consys-experts repo | Future |
| FW-02-4 | 實現完整的 `Think → Plan → Act → Learn` 循環 | Future |

**參考實作**：[claude-mem](https://github.com/thedotmack/claude-mem)

---

## 10. 參考資料

### 核心概念

| 資料 | 說明 |
|------|------|
| [Harness Engineering（Martin Fowler Blog）](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html) | 本系統架構核心啟發 |
| [AgentShield](https://github.com/affaan-m/agentshield) | Agent 安全審計參考實作（FW-01）|
| [claude-memory-engine](https://github.com/HelloRuru/claude-memory-engine) | Hooks 設計參考，8-step 學習循環 |
| [claude-mem](https://github.com/thedotmack/claude-mem) | 輕量記憶系統，memory → learn 參考（FW-02）|

### 延伸閱讀（個人知識庫，連結待更新為個人網站）

| 資料 | 說明 |
|------|------|
| [Lessons from Building Claude Code — How We Use Skills](https://github.com/swchen44/personal-knowledge-base-from-ai/blob/main/AI/2026-03-17-LESSONS-FROM-BUILDING-CLAUDE-CODE-HOW-WE-USE-SKILLS.md) | 實戰經驗：Claude Code 中 Skills 的使用心得 |
| [5 Agent Skill Design Patterns Every ADK Developer Should Know](https://github.com/swchen44/personal-knowledge-base-from-ai/blob/main/AI/2026-03-18-5-AGENT-SKILL-DESIGN-PATTERNS-EVERY-ADK-DEVELOPER-SHOULD-KNOW.md) | ADK 開發者必知的 5 種 Skill 設計模式 |
| [Claude-mem Code Analysis](https://github.com/swchen44/personal-knowledge-base-from-ai/blob/main/CodeAnalysis/2025-08-31-CLAUDE-MEM-CODE-ANALYSIS.md) | claude-mem 原始碼深度分析 |
