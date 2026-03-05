"""
測試 pdf_to_markdown.py 的核心函式
（不需要 PDF 檔案即可執行）
"""

import pytest
from pdf_to_markdown import _clean_cell, table_to_markdown


# ---------------------------------------------------------------------------
# _clean_cell
# ---------------------------------------------------------------------------

class TestCleanCell:
    """驗證 _clean_cell 的各種輸入情況。"""

    def test_none_returns_empty(self):
        """None 輸入應回傳空字串。"""
        assert _clean_cell(None) == ""

    def test_strips_whitespace(self):
        """前後空白應被去除。"""
        assert _clean_cell("  hello  ") == "hello"

    def test_collapses_newlines(self):
        """換行符號應轉為單一空格。"""
        assert _clean_cell("line1\nline2") == "line1 line2"

    def test_collapses_multiple_spaces(self):
        """多個連續空白應壓縮為一個。"""
        assert _clean_cell("a   b") == "a b"

    def test_numeric_cell(self):
        """數字應轉換為字串。"""
        assert _clean_cell(42) == "42"

    def test_empty_string(self):
        """空字串應原樣回傳。"""
        assert _clean_cell("") == ""


# ---------------------------------------------------------------------------
# table_to_markdown
# ---------------------------------------------------------------------------

class TestTableToMarkdown:
    """驗證 table_to_markdown 的輸出格式正確性。"""

    def test_empty_returns_empty(self):
        """空輸入應回傳空字串。"""
        assert table_to_markdown([]) == ""

    def test_header_only(self):
        """僅有標頭時應產生標頭列與分隔列。"""
        result = table_to_markdown([["A", "B"]])
        lines = result.splitlines()
        assert lines[0] == "| A | B |"
        assert lines[1] == "| --- | --- |"
        assert len(lines) == 2

    def test_header_and_one_row(self):
        """標頭加一列資料應完整輸出三行。"""
        result = table_to_markdown([["Name", "Score"], ["Alice", "95"]])
        lines = result.splitlines()
        assert lines[0] == "| Name | Score |"
        assert lines[1] == "| --- | --- |"
        assert lines[2] == "| Alice | 95 |"

    def test_none_cells_become_empty(self):
        """None 儲存格應轉為空字串。"""
        result = table_to_markdown([["A", "B"], [None, "val"]])
        assert "| --- | --- |" in result
        assert "|  | val |" in result

    def test_short_row_padded(self):
        """資料列比標頭短時，應自動補齊空欄。"""
        result = table_to_markdown([["A", "B", "C"], ["only_one"]])
        last_line = result.splitlines()[-1]
        assert last_line.count("|") == 4  # 3 欄 + 首尾各 1

    def test_multiline_cell_collapsed(self):
        """儲存格內換行應壓縮為單行。"""
        result = table_to_markdown([["Header"], ["line1\nline2"]])
        assert "line1 line2" in result

    def test_multiple_rows(self):
        """多列資料應全數輸出。"""
        rows = [["X", "Y"], ["1", "2"], ["3", "4"]]
        lines = table_to_markdown(rows).splitlines()
        assert len(lines) == 4  # header + separator + 2 data rows

    def test_pipe_characters_in_cell(self):
        """確保管道符號不影響欄數計算（不需要跳脫）。"""
        result = table_to_markdown([["A"], ["a|b"]])
        assert "a|b" in result


# ---------------------------------------------------------------------------
# 執行
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
