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
    def test_none_returns_empty(self):
        assert _clean_cell(None) == ""

    def test_strips_whitespace(self):
        assert _clean_cell("  hello  ") == "hello"

    def test_collapses_newlines(self):
        assert _clean_cell("line1\nline2") == "line1 line2"

    def test_collapses_multiple_spaces(self):
        assert _clean_cell("a   b") == "a b"

    def test_numeric_cell(self):
        assert _clean_cell(42) == "42"

    def test_empty_string(self):
        assert _clean_cell("") == ""


# ---------------------------------------------------------------------------
# table_to_markdown
# ---------------------------------------------------------------------------

class TestTableToMarkdown:
    def test_empty_returns_empty(self):
        assert table_to_markdown([]) == ""

    def test_header_only(self):
        result = table_to_markdown([["A", "B"]])
        lines = result.splitlines()
        assert lines[0] == "| A | B |"
        assert lines[1] == "| --- | --- |"
        assert len(lines) == 2

    def test_header_and_one_row(self):
        result = table_to_markdown([["Name", "Score"], ["Alice", "95"]])
        lines = result.splitlines()
        assert lines[0] == "| Name | Score |"
        assert lines[1] == "| --- | --- |"
        assert lines[2] == "| Alice | 95 |"

    def test_none_cells_become_empty(self):
        result = table_to_markdown([["A", "B"], [None, "val"]])
        assert "| --- | --- |" in result
        assert "|  | val |" in result

    def test_short_row_padded(self):
        """資料列比標頭短時，應自動補齊空欄。"""
        result = table_to_markdown([["A", "B", "C"], ["only_one"]])
        last_line = result.splitlines()[-1]
        assert last_line.count("|") == 4  # 3 欄 + 首尾各 1

    def test_multiline_cell_collapsed(self):
        result = table_to_markdown([["Header"], ["line1\nline2"]])
        assert "line1 line2" in result

    def test_multiple_rows(self):
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
