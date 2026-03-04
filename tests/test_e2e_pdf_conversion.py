"""
E2E 測試：pdf_to_markdown.py 的完整轉換流程
============================================

使用 tests/fixtures/sample_with_tables_and_images.pdf 作為測試輸入。
該 PDF 有 3 頁，包含：
  - 員工薪資表格（第 1 頁）
  - 彩色長條圖圖片 + 產品庫存表格（第 2 頁）
  - 部門統計表格（含空欄位邊界情況，第 3 頁）

若 fixture PDF 不存在，conftest 會自動產生。
"""

import re
import shutil
import tempfile
from pathlib import Path

import pytest

# 嘗試在有/無 pdfplumber & fitz 的環境下均能 import
try:
    from pdf_to_markdown import PDFToMarkdown, table_to_markdown
    CONVERTER_AVAILABLE = True
except ImportError:
    CONVERTER_AVAILABLE = False

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "sample_with_tables_and_images.pdf"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def ensure_fixture_pdf():
    """若 fixture PDF 不存在，自動呼叫 make_fixture_pdf.py 產生。"""
    if not FIXTURE_PDF.exists():
        from tests.fixtures.make_fixture_pdf import make_pdf
        make_pdf()
    assert FIXTURE_PDF.exists(), f"Fixture PDF 不存在：{FIXTURE_PDF}"


@pytest.fixture()
def tmp_output(tmp_path):
    """提供一個隔離的暫存目錄，每個測試獨立。"""
    return tmp_path


@pytest.fixture()
def converter(tmp_output):
    """建立 PDFToMarkdown 實例（圖片存至暫存目錄）。"""
    return PDFToMarkdown(
        pdf_path=str(FIXTURE_PDF),
        output_path=str(tmp_output / "output.md"),
        image_dir=str(tmp_output / "images"),
    )


# ---------------------------------------------------------------------------
# 跳過條件
# ---------------------------------------------------------------------------

skip_if_no_converter = pytest.mark.skipif(
    not CONVERTER_AVAILABLE,
    reason="pdfplumber 或 pymupdf 未安裝",
)


# ---------------------------------------------------------------------------
# E2E：基本轉換
# ---------------------------------------------------------------------------

@skip_if_no_converter
class TestBasicConversion:
    def test_output_file_created(self, converter, tmp_output):
        """轉換後應產生 .md 檔案。"""
        converter.convert()
        assert (tmp_output / "output.md").exists()

    def test_output_not_empty(self, converter, tmp_output):
        """輸出 Markdown 不得為空。"""
        md = converter.convert()
        assert len(md.strip()) > 100

    def test_output_is_valid_utf8(self, converter, tmp_output):
        """輸出應為合法 UTF-8 文字。"""
        converter.convert()
        content = (tmp_output / "output.md").read_text(encoding="utf-8")
        assert content  # 讀取成功即為合法 UTF-8

    def test_page_separators_present(self, converter):
        """多頁 PDF 應以 --- 分隔。"""
        md = converter.convert()
        assert "---" in md


# ---------------------------------------------------------------------------
# E2E：表格結構驗證
# ---------------------------------------------------------------------------

@skip_if_no_converter
class TestTableExtraction:
    """確認三張表格都正確擷取為 Markdown 格式。"""

    @pytest.fixture(autouse=True)
    def run_conversion(self, converter):
        self.md = converter.convert()

    # --- 格式驗證 ---

    def test_markdown_table_format_present(self):
        """Markdown 中應出現管道符號（表格格式）。"""
        assert "|" in self.md

    def test_table_separator_rows_present(self):
        """所有表格都應有 | --- | 分隔行。"""
        separators = re.findall(r"\|[\s\-|]+\|", self.md)
        assert len(separators) >= 3, f"應有 >=3 個分隔行，實際：{len(separators)}"

    # --- 表格 1：員工薪資（第 1 頁）---

    def test_salary_table_headers(self):
        """員工薪資表格應包含欄位標頭關鍵字。"""
        assert "Name" in self.md or "Employee" in self.md

    def test_salary_table_employee_names(self):
        """員工姓名應出現在輸出中。"""
        found = sum(name in self.md for name in ["Alice", "Bob", "Carol", "David", "Eva"])
        assert found >= 3, f"員工姓名辨識不足，只找到 {found}/5"

    def test_salary_table_numeric_values(self):
        """薪資數字應保留在表格中。"""
        assert "95,000" in self.md or "95000" in self.md

    # --- 表格 2：產品庫存（第 2 頁）---

    def test_inventory_table_skus(self):
        """產品 SKU 應出現在輸出中。"""
        found = sum(sku in self.md for sku in ["P-101", "P-202", "P-303"])
        assert found >= 2, f"SKU 辨識不足，只找到 {found}/3"

    def test_inventory_table_prices(self):
        """單價欄位應保留。"""
        assert "$49.99" in self.md or "49.99" in self.md

    # --- 表格 3：部門統計（第 3 頁）---

    def test_statistics_table_departments(self):
        """部門名稱應出現在輸出中。"""
        found = sum(dept in self.md for dept in ["Engineering", "Product", "Design", "Finance"])
        assert found >= 3, f"部門辨識不足，只找到 {found}/4"

    def test_statistics_table_budget_values(self):
        """預算欄位應保留。"""
        assert "$4.5M" in self.md or "4.5M" in self.md

    # --- 表格數量 ---

    def test_at_least_three_tables_found(self):
        """全文應至少有 3 個獨立表格（含分隔行）。"""
        # 計算含 | --- | 的行數，每張表格恰好 1 行
        sep_lines = [
            line for line in self.md.splitlines()
            if re.fullmatch(r"(\|[\s\-]+)+\|", line.strip())
        ]
        assert len(sep_lines) >= 3, f"找到 {len(sep_lines)} 個表格分隔行，期望 >=3"


# ---------------------------------------------------------------------------
# E2E：圖片擷取驗證（儲存為檔案）
# ---------------------------------------------------------------------------

@skip_if_no_converter
class TestImageExtraction:
    """確認第 2 頁的圖片被正確擷取。"""

    @pytest.fixture(autouse=True)
    def run_conversion(self, converter, tmp_output):
        self.md = converter.convert()
        self.image_dir = tmp_output / "images"

    def test_image_dir_created(self):
        """圖片目錄應自動建立。"""
        assert self.image_dir.exists()

    def test_at_least_one_image_extracted(self):
        """至少擷取出 1 張圖片檔案。"""
        images = list(self.image_dir.glob("*"))
        assert len(images) >= 1, f"圖片目錄為空：{self.image_dir}"

    def test_image_files_are_valid_size(self):
        """擷取的圖片不得為空檔案。"""
        for img in self.image_dir.glob("*"):
            assert img.stat().st_size > 100, f"圖片疑似損壞（太小）：{img}"

    def test_markdown_contains_image_reference(self):
        """Markdown 應包含圖片語法 ![]()。"""
        assert "![" in self.md


# ---------------------------------------------------------------------------
# E2E：base64 嵌入圖片模式
# ---------------------------------------------------------------------------

@skip_if_no_converter
class TestBase64ImageMode:
    def test_embed_images_base64(self, tmp_output):
        """--embed-images 模式：圖片應以 data URI 嵌入 Markdown。"""
        conv = PDFToMarkdown(
            pdf_path=str(FIXTURE_PDF),
            output_path=str(tmp_output / "embedded.md"),
            embed_images=True,
        )
        md = conv.convert()
        assert "data:image/" in md, "應包含 base64 data URI"
        assert ";base64," in md


# ---------------------------------------------------------------------------
# E2E：邊界情況
# ---------------------------------------------------------------------------

@skip_if_no_converter
class TestEdgeCases:
    def test_empty_cells_do_not_crash(self, tmp_output):
        """含空欄位的表格（第 3 頁）不應導致例外。"""
        conv = PDFToMarkdown(
            pdf_path=str(FIXTURE_PDF),
            output_path=str(tmp_output / "edge.md"),
        )
        md = conv.convert()  # 不拋出例外即通過
        assert md

    def test_file_not_found_raises(self, tmp_output):
        """輸入不存在的 PDF 應拋出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            PDFToMarkdown(pdf_path="nonexistent.pdf")

    def test_output_path_parent_dir_created(self, tmp_output):
        """輸出路徑的父目錄不存在時，應自動建立。"""
        nested_out = tmp_output / "nested" / "dir" / "output.md"
        conv = PDFToMarkdown(
            pdf_path=str(FIXTURE_PDF),
            output_path=str(nested_out),
        )
        conv.convert()
        assert nested_out.exists()
