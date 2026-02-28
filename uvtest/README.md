# uvtest

一個示範 Python 專案結構的範例，使用 [uv](https://github.com/astral-sh/uv) 管理套件，並結合 [PEP 723](https://peps.python.org/pep-0723/) inline script metadata。

## 專案結構

```
uvtest/
├── app/
│   ├── __init__.py
│   ├── main.py                  # 應用程式進入點（thin）
│   ├── config.py                # 集中管理設定
│   ├── services/
│   │   ├── __init__.py
│   │   └── greeting_service.py  # 業務邏輯
│   ├── models/                  # 資料模型（備用）
│   ├── routes/                  # API 路由（備用）
│   └── utils/                   # 通用工具（備用）
├── tests/
│   └── test_greeting_service.py
├── main.py                      # PEP 723 entry point
├── pyproject.toml
└── README.md
```

## 環境需求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

## 安裝

```bash
uv sync
```

## 執行

```bash
uv run main.py
```

執行後會看到牛說哈囉：

```
  __
| 哈囉 |
  ==
  \
   \
     ^__^
     (oo)\_______
     (__)\       )\/\
         ||----w |
         ||     ||
```

## 測試

使用 Python 內建的 `unittest`：

```bash
uv run python -m unittest discover -v
```

## 套件說明

| 套件 | 用途 |
|------|------|
| `cowsay` | 產生 ASCII 牛的輸出 |
| `ruff` | 程式碼格式化與 lint |

## 設計原則

- **Entry point thin** — `main.py` 只負責呼叫，不含業務邏輯
- **業務邏輯集中在 services/** — 便於測試與重用
- **Tests 獨立於 app/** — 清楚分離，易於 CI 整合
- **PEP 723** — script 直接宣告相依套件，可獨立執行
