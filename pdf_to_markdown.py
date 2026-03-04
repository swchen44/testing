#!/usr/bin/env python3
"""
PDF to Markdown Converter
=========================
支援表格、圖片的 PDF 轉 Markdown 工具

主要使用的函式庫：
  - pdfplumber  : 高精度表格擷取
  - pymupdf     : 圖片擷取與文字解析
  - camelot     : 複雜表格（需 ghostscript）
  - Pillow      : 圖片處理

安裝：
  pip install pdfplumber pymupdf pillow camelot-py[cv] ghostscript
"""

import argparse
import base64
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import camelot
except ImportError:
    camelot = None


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def _clean_cell(cell: str | None) -> str:
    """清除儲存格中的換行與多餘空白。"""
    if cell is None:
        return ""
    return re.sub(r"\s+", " ", str(cell)).strip()


def table_to_markdown(rows: list[list]) -> str:
    """將二維陣列轉換為 Markdown 表格字串。"""
    if not rows:
        return ""

    # 標頭
    header = [_clean_cell(c) for c in rows[0]]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]
    for row in rows[1:]:
        cells = [_clean_cell(c) for c in row]
        # 補齊欄數
        while len(cells) < len(header):
            cells.append("")
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def extract_images_from_page(page, output_dir: Path, page_num: int) -> list[str]:
    """
    從 PyMuPDF 的頁面擷取圖片，儲存至 output_dir，
    回傳 Markdown image 標記清單。
    """
    if fitz is None:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    md_images = []
    image_list = page.get_images(full=True)

    for img_index, img_info in enumerate(image_list):
        xref = img_info[0]
        try:
            base_image = page.parent.extract_image(xref)
        except Exception:
            continue

        img_bytes = base_image["image"]
        ext = base_image.get("ext", "png")
        img_filename = f"page{page_num + 1}_img{img_index + 1}.{ext}"
        img_path = output_dir / img_filename

        img_path.write_bytes(img_bytes)
        md_images.append(f"![圖片 {img_index + 1}]({img_path})")

    return md_images


# ---------------------------------------------------------------------------
# Core converter
# ---------------------------------------------------------------------------

class PDFToMarkdown:
    """
    PDF → Markdown 轉換器

    策略：
    1. 用 pdfplumber 偵測 & 擷取表格（準確度高）
    2. 用 PyMuPDF 擷取頁面文字（保留順序）& 圖片
    3. 將表格插入對應位置
    4. 可選用 camelot 處理複雜/掃描型表格
    """

    def __init__(
        self,
        pdf_path: str,
        output_path: str | None = None,
        image_dir: str | None = None,
        use_camelot: bool = False,
        embed_images: bool = False,
    ):
        self.pdf_path = Path(pdf_path)
        self.output_path = Path(output_path) if output_path else self.pdf_path.with_suffix(".md")
        self.image_dir = Path(image_dir) if image_dir else self.pdf_path.parent / "images"
        self.use_camelot = use_camelot and camelot is not None
        self.embed_images = embed_images  # True = base64 inline；False = 檔案路徑

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"找不到 PDF：{self.pdf_path}")
        if pdfplumber is None:
            raise ImportError("請先安裝 pdfplumber：pip install pdfplumber")
        if fitz is None:
            raise ImportError("請先安裝 PyMuPDF：pip install pymupdf")

    # ------------------------------------------------------------------
    def convert(self) -> str:
        """執行轉換，回傳 Markdown 字串並寫入檔案。"""
        print(f"[*] 開始轉換：{self.pdf_path}")
        md_pages = []

        with pdfplumber.open(self.pdf_path) as plumber_pdf:
            fitz_pdf = fitz.open(str(self.pdf_path))
            total = len(plumber_pdf.pages)

            for page_num in range(total):
                print(f"    處理第 {page_num + 1}/{total} 頁 ...", end="\r")
                plumber_page = plumber_pdf.pages[page_num]
                fitz_page = fitz_pdf[page_num]

                page_md = self._process_page(plumber_page, fitz_page, page_num)
                md_pages.append(page_md)

            fitz_pdf.close()

        print(f"\n[*] 完成，共 {total} 頁")
        full_md = "\n\n---\n\n".join(filter(None, md_pages))
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(full_md, encoding="utf-8")
        print(f"[*] 已儲存至：{self.output_path}")
        return full_md

    # ------------------------------------------------------------------
    def _process_page(self, plumber_page, fitz_page, page_num: int) -> str:
        """處理單頁，回傳該頁的 Markdown 字串。"""
        parts = []

        # 1. 擷取表格區域（bounding box）
        tables_md, table_bboxes = self._extract_tables(plumber_page, page_num)

        # 2. 擷取文字（排除表格區域）
        text_blocks = self._extract_text_blocks(fitz_page, table_bboxes)

        # 3. 擷取圖片
        images_md = self._extract_images(fitz_page, page_num)

        # 4. 合併：文字 → 表格（依頁面垂直順序插入）
        parts.extend(text_blocks)
        if tables_md:
            parts.append("\n".join(tables_md))
        if images_md:
            parts.extend(images_md)

        return "\n\n".join(filter(None, parts))

    # ------------------------------------------------------------------
    def _extract_tables(self, plumber_page, page_num: int) -> tuple[list[str], list]:
        """使用 pdfplumber 擷取表格，回傳 (markdown_list, bbox_list)。"""
        tables_md = []
        bboxes = []

        # pdfplumber 原生表格偵測
        for table in plumber_page.extract_tables():
            if table:
                tables_md.append(table_to_markdown(table))

        # pdfplumber 取得表格 bbox（用來在文字擷取時排除）
        for t in plumber_page.find_tables():
            bboxes.append(t.bbox)  # (x0, top, x1, bottom)

        # 可選：使用 camelot 進一步處理（適合複雜表格）
        if self.use_camelot and not tables_md:
            tables_md.extend(self._extract_tables_camelot(page_num + 1))

        return tables_md, bboxes

    def _extract_tables_camelot(self, page_num: int) -> list[str]:
        """使用 camelot 擷取表格（備用，適合格線型表格）。"""
        results = []
        try:
            # 'lattice' 適合有格線表格；'stream' 適合無格線
            for flavor in ("lattice", "stream"):
                tables = camelot.read_pdf(
                    str(self.pdf_path),
                    pages=str(page_num),
                    flavor=flavor,
                )
                for tbl in tables:
                    df = tbl.df
                    rows = [df.columns.tolist()] + df.values.tolist()
                    results.append(table_to_markdown(rows))
                if results:
                    break
        except Exception as e:
            print(f"\n[!] camelot 擷取失敗（頁 {page_num}）：{e}")
        return results

    # ------------------------------------------------------------------
    def _extract_text_blocks(self, fitz_page, table_bboxes: list) -> list[str]:
        """
        使用 PyMuPDF 擷取文字區塊，
        跳過與表格重疊的區域。
        """
        blocks = []
        raw_blocks = fitz_page.get_text("blocks")  # (x0,y0,x1,y1,text,block_no,type)

        for blk in raw_blocks:
            x0, y0, x1, y1, text, *_ = blk
            if not text.strip():
                continue

            # 檢查是否在表格 bbox 內（pdfplumber 座標系需轉換）
            if self._overlaps_table(x0, y0, x1, y1, table_bboxes, fitz_page):
                continue

            cleaned = self._text_to_markdown(text)
            if cleaned:
                blocks.append(cleaned)

        return blocks

    def _overlaps_table(self, x0, y0, x1, y1, table_bboxes, fitz_page) -> bool:
        """判斷文字區塊是否與表格 bbox 重疊（座標系轉換）。"""
        if not table_bboxes:
            return False
        # pdfplumber 使用 PDF 座標（y 從下往上），PyMuPDF 從上往下
        page_height = fitz_page.rect.height
        for tb in table_bboxes:
            tx0, ttop, tx1, tbottom = tb
            # 轉換 pdfplumber top/bottom → fitz y0/y1
            ty0 = page_height - tbottom
            ty1 = page_height - ttop
            # 重疊判斷（IoU 簡化版：中心點在 bbox 內）
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if tx0 <= cx <= tx1 and ty0 <= cy <= ty1:
                return True
        return False

    @staticmethod
    def _text_to_markdown(text: str) -> str:
        """將純文字簡單格式化為 Markdown。"""
        text = text.strip()
        if not text:
            return ""
        # 移除多餘空行
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    # ------------------------------------------------------------------
    def _extract_images(self, fitz_page, page_num: int) -> list[str]:
        """擷取圖片，回傳 Markdown 圖片標記清單。"""
        if self.embed_images:
            return self._extract_images_base64(fitz_page, page_num)
        return extract_images_from_page(fitz_page, self.image_dir, page_num)

    def _extract_images_base64(self, fitz_page, page_num: int) -> list[str]:
        """將圖片轉為 base64 inline 嵌入。"""
        md_images = []
        for img_index, img_info in enumerate(fitz_page.get_images(full=True)):
            xref = img_info[0]
            try:
                base_image = fitz_page.parent.extract_image(xref)
            except Exception:
                continue
            img_bytes = base_image["image"]
            ext = base_image.get("ext", "png")
            b64 = base64.b64encode(img_bytes).decode()
            md_images.append(f"![圖片 {img_index + 1}](data:image/{ext};base64,{b64})")
        return md_images


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PDF 轉 Markdown（表格 + 圖片）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python pdf_to_markdown.py report.pdf
  python pdf_to_markdown.py report.pdf -o output.md --image-dir ./imgs
  python pdf_to_markdown.py report.pdf --camelot --embed-images
        """,
    )
    parser.add_argument("pdf", help="輸入的 PDF 檔案路徑")
    parser.add_argument("-o", "--output", help="輸出的 Markdown 路徑（預設與 PDF 同名）")
    parser.add_argument("--image-dir", help="圖片儲存目錄（預設：./images）")
    parser.add_argument(
        "--camelot",
        action="store_true",
        help="啟用 camelot 處理複雜表格（需安裝 camelot-py[cv] 與 ghostscript）",
    )
    parser.add_argument(
        "--embed-images",
        action="store_true",
        help="將圖片以 base64 嵌入 Markdown（適合單檔輸出）",
    )

    args = parser.parse_args()

    try:
        converter = PDFToMarkdown(
            pdf_path=args.pdf,
            output_path=args.output,
            image_dir=args.image_dir,
            use_camelot=args.camelot,
            embed_images=args.embed_images,
        )
        converter.convert()
    except (FileNotFoundError, ImportError) as e:
        print(f"[錯誤] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
