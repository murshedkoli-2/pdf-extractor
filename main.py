import argparse
import sys
import os
from src.extractor import PDFExtractor
from src.utils import setup_logging, save_to_json, validate_file
import logging

def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Bengali Voter List PDF to JSON Extractor")
    parser.add_argument("input_file", help="Path to input PDF file")
    parser.add_argument("--output", default="output_data.json", help="Path to output JSON file")
    parser.add_argument("--ocr", action="store_true", help="Force OCR usage")
    parser.add_argument("--pages", help="Pages to process (e.g., '1' or '1-5'). Default is all.", default=None)

    args = parser.parse_args()

    try:
        validate_file(args.input_file)
        
        logging.info(f"Starting extraction for {args.input_file}")
        
        extractor = PDFExtractor(args.input_file, use_ocr=args.ocr)
        
        # Parse page range if provided
        page_range = None
        if args.pages:
            if '-' in args.pages:
                start, end = map(int, args.pages.split('-'))
                page_range = range(start, end + 1)
            else:
                page_range = [int(args.pages)]

        data = extractor.process(pages=page_range)
        
        save_to_json(data, args.output)
        logging.info("Extraction complete.")

    except Exception as e:
        logging.error(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
