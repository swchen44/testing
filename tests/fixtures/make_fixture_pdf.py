"""
產生測試用 PDF fixture：sample_with_tables_and_images.pdf

內容：
  - 第 1 頁：標題文字 + 員工薪資表格 + 說明段落
  - 第 2 頁：產品庫存表格 + 嵌入彩色圖片 (圓餅圖)
  - 第 3 頁：多欄位統計表格（含 None / 空值邊界情況）

執行：
  python tests/fixtures/make_fixture_pdf.py
"""

from pathlib import Path
import io
from fpdf import FPDF, XPos, YPos
from PIL import Image, ImageDraw

OUTPUT = Path(__file__).parent / "sample_with_tables_and_images.pdf"


# ---------------------------------------------------------------------------
# 1. 建立彩色測試圖片（PIL）
# ---------------------------------------------------------------------------

def _make_bar_chart_image() -> io.BytesIO:
    """產生一張簡單的長條圖 PNG，尺寸 400x200。"""
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    bars = [
        ("Q1", 80,  (70,  130, 180)),
        ("Q2", 140, (255, 165,  0)),
        ("Q3", 110, (60,  179, 113)),
        ("Q4", 170, (220,  20,  60)),
    ]
    base_y = 170
    bar_w  = 60
    gap    = 40

    for i, (label, height, color) in enumerate(bars):
        x = gap + i * (bar_w + gap)
        draw.rectangle([x, base_y - height, x + bar_w, base_y], fill=color)
        draw.text((x + 10, base_y + 4), label, fill=(0, 0, 0))

    draw.text((10, 8), "Quarterly Revenue", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# 2. 建立 PDF
# ---------------------------------------------------------------------------

def make_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ------------------------------------------------------------------
    # 第 1 頁：員工薪資表格
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Annual Employee Salary Report 2024", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7, (
        "This report summarizes the annual salary and performance bonus "
        "for all full-time employees in the engineering department."
    ))
    pdf.ln(4)

    # 表格 1：員工薪資
    headers = ["Employee ID", "Name", "Department", "Salary (USD)", "Bonus (%)"]
    rows = [
        ["E001", "Alice Chen",   "Backend",  "95,000",  "12"],
        ["E002", "Bob Smith",    "Frontend", "88,000",  "10"],
        ["E003", "Carol Wang",   "Data",     "102,000", "15"],
        ["E004", "David Lee",    "DevOps",   "91,000",  "11"],
        ["E005", "Eva Martinez", "Backend",  "97,000",  "13"],
    ]
    col_widths = [28, 38, 30, 36, 28]

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(70, 130, 180)
    pdf.set_text_color(255, 255, 255)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 8, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    for i, row in enumerate(rows):
        fill = i % 2 == 0
        pdf.set_fill_color(235, 245, 255) if fill else pdf.set_fill_color(255, 255, 255)
        for w, cell in zip(col_widths, row):
            pdf.cell(w, 7, cell, border=1, fill=True)
        pdf.ln()

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 6, "* Bonus percentage subject to final Q4 review.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ------------------------------------------------------------------
    # 第 2 頁：圖片 + 產品庫存表格
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Product Inventory & Revenue Chart", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(2)

    # 嵌入圖片
    chart_buf = _make_bar_chart_image()
    pdf.image(chart_buf, x=30, y=pdf.get_y(), w=150)
    pdf.ln(60)

    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, (
        "Figure 1: Quarterly revenue chart for FY2024. "
        "Q4 showed the strongest performance driven by holiday sales."
    ))
    pdf.ln(4)

    # 表格 2：產品庫存
    headers2 = ["SKU", "Product Name", "Category", "Stock", "Unit Price"]
    rows2 = [
        ["P-101", "Wireless Keyboard", "Peripherals", "342",  "$49.99"],
        ["P-202", "USB-C Hub 7-in-1",  "Accessories", "210",  "$35.00"],
        ["P-303", "27\" Monitor",       "Displays",    "88",   "$299.00"],
        ["P-404", "Mechanical Mouse",   "Peripherals", "560",  "$29.99"],
        ["P-505", "Laptop Stand",       "Accessories", "415",  "$24.50"],
        ["P-606", "Webcam 4K",          "Cameras",     "130",  "$89.00"],
    ]
    col_widths2 = [22, 50, 32, 22, 30]

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(60, 179, 113)
    pdf.set_text_color(255, 255, 255)
    for w, h in zip(col_widths2, headers2):
        pdf.cell(w, 8, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    for i, row in enumerate(rows2):
        fill = i % 2 == 0
        pdf.set_fill_color(235, 255, 240) if fill else pdf.set_fill_color(255, 255, 255)
        for w, cell in zip(col_widths2, row):
            pdf.cell(w, 7, cell, border=1, fill=True)
        pdf.ln()

    # ------------------------------------------------------------------
    # 第 3 頁：統計摘要表（含空值邊界情況）
    # ------------------------------------------------------------------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Department Statistics Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, (
        "The following table contains department-level statistics. "
        "Some fields may be empty where data collection is pending."
    ))
    pdf.ln(4)

    # 表格 3（含空欄位）
    headers3 = ["Department", "Headcount", "Avg Salary", "Attrition %", "Budget"]
    rows3 = [
        ["Engineering",  "45", "$98,500",  "4.2",  "$4.5M"],
        ["Product",      "18", "$105,000", "3.8",  "$1.9M"],
        ["Design",       "12", "$92,000",  "",     "$1.1M"],   # 空 Attrition
        ["Marketing",    "22", "$78,000",  "6.1",  ""],        # 空 Budget
        ["HR",           "8",  "",         "2.0",  "$0.8M"],   # 空 Avg Salary
        ["Finance",      "10", "$88,000",  "3.5",  "$0.9M"],
    ]
    col_widths3 = [36, 26, 30, 28, 28]

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(220, 20, 60)
    pdf.set_text_color(255, 255, 255)
    for w, h in zip(col_widths3, headers3):
        pdf.cell(w, 8, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    for i, row in enumerate(rows3):
        fill = i % 2 == 0
        pdf.set_fill_color(255, 240, 240) if fill else pdf.set_fill_color(255, 255, 255)
        for w, cell in zip(col_widths3, row):
            pdf.cell(w, 7, cell, border=1, fill=True)
        pdf.ln()

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "End of Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    # ------------------------------------------------------------------
    pdf.output(str(OUTPUT))
    print(f"[ok] PDF 已產生：{OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    make_pdf()
