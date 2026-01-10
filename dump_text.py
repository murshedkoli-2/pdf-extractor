from src.extractor import PDFExtractor
import logging
import sys

# Setup simple console logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def dump_page_text(pdf_path, page_num):
    extractor = PDFExtractor(pdf_path, use_ocr=True)
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        text = extractor._extract_text_from_page(pdf, page_num - 1)
        with open("full_text_utf8.txt", "w", encoding="utf-8") as f:
            f.write(f"--- START PAGE {page_num} ---\n")
            f.write(text)
            f.write(f"\n--- END PAGE {page_num} ---\n")
            print("Done writing to full_text_utf8.txt")

if __name__ == "__main__":
    dump_page_text("sample.pdf.pdf", 3)
