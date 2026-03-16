# Here is a testing repo, playground repo

# C Code Scanner

This project provides a Python script to scan C source code for potential bugs and memory inefficiencies using AI models.

## 1. User Manual

To use the script, you need to have Python installed. You also need to set the `GOOGLE_API_KEY` or `OPENAI_API_KEY` environment variable with your API key.

1.  Install the required Python libraries:

    ```bash
    pip install google-generativeai openai
    ```

2.  Run the script:

    ```bash
    python c_code_scanner.py --model gemini|openai <c_code_file> <prompt_file> <output_csv_file>
    ```

    *   `<c_code_file>`: Path to the C source code file (default: defective.c).
    *   `<prompt_file>`: Path to the prompt file (default: prompt.txt).
    *   `<output_csv_file>`: Path to the output CSV file (default: output.csv).
    *   `--model`: Choose the AI model to use (gemini or openai). Default is gemini.

    Example:

    ```bash
    python c_code_scanner.py --model gemini defective.c prompt.txt output.csv
    ```

## 2. Code Architecture

The project consists of the following main components:

*   `c_code_scanner.py`: The main Python script that performs the C code scanning.
*   `AIModel`: Abstract base class for AI models.
*   `GeminiAIModel`: Concrete class for the Gemini AI model.
*   `OpenAIModel`: Concrete class for the OpenAI model.
*   `get_ai_response`: Function to get the AI response for a given C code line and prompt.
*   `scan_c_code`: Function to scan the C code and generate the CSV output.

## 3. File and Folder Description

*   `c_code_scanner.py`: Contains the main Python script.
*   `defective.c`: Contains example defective C code.
*   `prompt.txt`: Contains the prompt for the AI model.
*   `output.csv`: Contains the output of the C code scan in CSV format.
*   `README.md`: This file.

---

# PDF to Markdown Converter

將 PDF 轉換為 Markdown，**特別針對表格與圖片**做完整處理。

## 快速開始（uv，免手動安裝套件）

本工具使用 [PEP 723](https://peps.python.org/pep-0723/) inline script metadata，
搭配 [uv](https://docs.astral.sh/uv/) 可一行執行，自動建立隔離環境並安裝依賴。

```bash
# 安裝 uv（若尚未安裝）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 直接執行，uv 自動安裝所需套件
uv run pdf_to_markdown.py report.pdf

# 指定輸出路徑與圖片目錄
uv run pdf_to_markdown.py report.pdf -o output.md --image-dir ./images

# 圖片以 base64 嵌入單一 Markdown 檔
uv run pdf_to_markdown.py report.pdf --embed-images

# 啟用 camelot 處理複雜格線型表格（需另裝 ghostscript）
uv run pdf_to_markdown.py report.pdf --camelot
```

## 傳統方式（pip）

```bash
pip install pdfplumber pymupdf pillow
python pdf_to_markdown.py report.pdf
```

## 輸出範例

輸入 PDF 中的表格會轉換為標準 Markdown：

```markdown
| Employee ID | Name       | Department | Salary (USD) | Bonus (%) |
| ---         | ---        | ---        | ---          | ---       |
| E001        | Alice Chen | Backend    | 95,000       | 12        |
| E002        | Bob Smith  | Frontend   | 88,000       | 10        |
```

圖片會擷取至 `--image-dir` 目錄（預設 `./images/`），並在 Markdown 中以相對路徑引用：

```markdown
![圖片 1](images/page2_img1.png)
```

## CLI 參數說明

| 參數 | 說明 | 預設值 |
| --- | --- | --- |
| `pdf` | 輸入 PDF 路徑 | （必填） |
| `-o`, `--output` | 輸出 Markdown 路徑 | 與 PDF 同名，副檔名 `.md` |
| `--image-dir` | 圖片儲存目錄 | `./images/` |
| `--camelot` | 啟用 camelot 處理複雜表格 | 關閉 |
| `--embed-images` | 圖片以 base64 嵌入 Markdown | 關閉 |

## 套件依賴策略

| 函式庫 | 用途 | 必裝 |
| --- | --- | --- |
| `pdfplumber` | 高精度表格偵測與擷取 | ✅ |
| `pymupdf` (`fitz`) | 文字區塊 & 圖片擷取 | ✅ |
| `pillow` | 圖片處理 | ✅ |
| `camelot-py[cv]` | 複雜格線型表格（需 ghostscript） | 選裝 |
| `marker-pdf` | 最高精度轉換（支援 GPU） | 選裝 |

## 開發流程

### 環境設置

```bash
# 安裝開發與測試工具
pip install pdfplumber pymupdf pillow fpdf2 pytest pylint

# 或直接用 uv 建立虛擬環境
uv venv && uv pip install pdfplumber pymupdf pillow fpdf2 pytest pylint
```

### 產生測試 Fixture PDF

```bash
# 產生含表格與圖片的 3 頁測試 PDF
uv run tests/fixtures/make_fixture_pdf.py
# 或
python tests/fixtures/make_fixture_pdf.py
```

### 執行測試

```bash
# 全部測試（單元 + E2E）
python -m pytest -v

# 只跑 E2E 測試
python -m pytest tests/test_e2e_pdf_conversion.py -v

# 只跑核心函式單元測試
python -m pytest test_pdf_to_markdown.py -v
```

### 程式碼品質檢查（pylint）

本專案目標維持 pylint **10.00/10**：

```bash
pylint pdf_to_markdown.py tests/test_e2e_pdf_conversion.py test_pdf_to_markdown.py
```

pylint 設定檔：`.pylintrc`（調整 pytest fixture 相關例外規則，max-args=8）。

### 專案結構

```
pdf_to_markdown.py              # 主工具（PEP 723 inline metadata）
requirements_pdf.txt            # 套件清單
.pylintrc                       # pylint 設定
tests/
  test_e2e_pdf_conversion.py    # E2E 測試（22 個）
  fixtures/
    make_fixture_pdf.py         # Fixture PDF 產生腳本（PEP 723）
    sample_with_tables_and_images.pdf
test_pdf_to_markdown.py         # 核心函式單元測試（14 個）
```

---

## 4. Copyright Apache 2

Copyright 2025 [Your Name]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
