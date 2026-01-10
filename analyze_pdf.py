import pdfplumber
import sys

def analyze(pdf_path):
    print(f"Analyzing: {pdf_path}")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                print("No pages found.")
                return

            page = pdf.pages[0]
            text = page.extract_text()
            
            print(f"--- Page 1 Stats ---")
            print(f"Width: {page.width}, Height: {page.height}")
            print(f"Objects: {len(page.chars)} chars, {len(page.rects)} rects, {len(page.lines)} lines")
            
            if text:
                print("\n--- Extracted Text (First 500 chars) ---")
                print(text[:500])
                print("\n--- End Text ---")
            else:
                print("\nNo text extracted. Likely an image scan.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze(sys.argv[1])
