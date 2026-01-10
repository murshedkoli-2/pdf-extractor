import json
import logging
import os

def setup_logging(log_file="extractor.log"):
    """Sets up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def bengali_to_int(bneg_str):
    """
    Converts Bengali numerals string to integer.
    Returns 0 if conversion fails.
    """
    if not bneg_str:
        return 0
    bn_map = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
    try:
        # Filter non-digits just in case
        clean_str = ''.join(filter(lambda x: x in "০১২৩৪৫৬৭৮৯0123456789", bneg_str))
        converted = clean_str.translate(bn_map)
        return int(converted)
    except ValueError:
        return 0

def save_to_json(data, output_path):
    """Saves data dictionary to JSON file with UTF-8 encoding."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"Data successfully saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save JSON: {e}")

def validate_file(file_path):
    """Checks if file exists and is a PDF."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.lower().endswith('.pdf'):
        raise ValueError("Invalid file format. Please provide a PDF file.")
    return True
