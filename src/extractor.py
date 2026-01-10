import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import logging
from src.parser import VoterParser

class PDFExtractor:
    def __init__(self, file_path, use_ocr=False):
        self.file_path = file_path
        self.use_ocr = use_ocr
        self.parser = VoterParser()

    def process(self, pages=None):
        """
        Main processing loop.
        pages: iterable of page numbers (1-based) to process. If None, process all.
        """
        all_voters = []

        try:
            with pdfplumber.open(self.file_path) as pdf:
                total_pages = len(pdf.pages)
                logging.info(f"PDF opened. Total pages: {total_pages}")
                
                # 1. Get Global Metadata from Page 1
                logging.info("Extracting Metadata from Page 1...")
                header_text = self._extract_text_from_page(pdf, 0)
                global_meta = self.parser.parse_header_page(header_text)
                logging.info(f"Extracted Metadata (Initial): {global_meta}")
                
                # 2. Process all pages
                pages_to_process = pages if pages else range(1, total_pages + 1)
                
                for page_num in pages_to_process:
                    if page_num > total_pages: continue
                    
                    logging.info(f"Processing page {page_num}...")
                    page_text = self._extract_text_from_page(pdf, page_num - 1)
                    
                    if not page_text:
                        continue
                        
                    page_voters = self.parser.parse_text_page(page_text, global_meta=global_meta)
                    if page_voters:
                        all_voters.extend(page_voters)
            
            # 3. Post-Processing: Backfill missing keys (District)
            if all_voters:
                # Check directly on the first voter since meta is merged into them
                first_voter = all_voters[0]
                missing_district = 'district' not in first_voter or not first_voter['district']
                
                inferred_district = None
                if missing_district and 'address' in first_voter:
                    # Heuristic: Address is "Village, Upazila, District"
                    parts = first_voter['address'].split(',')
                    if len(parts) >= 3:
                        inferred_district = parts[-1].strip()
                        logging.info(f"Inferred missing District from address: {inferred_district}")
                
                if missing_district and inferred_district:
                    for v in all_voters:
                        v['district'] = inferred_district
            
            # 3.5 Deduplicate (Due to overlapping crops)
            if all_voters:
                unique_voters = {}
                for v in all_voters:
                    s_no = v.get('serial_no')
                    if not s_no:
                        # Fallback to voter_id if serial missing
                        s_no = v.get('voter_id', str(id(v)))
                    
                    if s_no in unique_voters:
                        # Combine/Prefer better one
                        existing = unique_voters[s_no]
                        # Score by number of keys with values
                        score_ex = sum(1 for k, val in existing.items() if val)
                        score_new = sum(1 for k, val in v.items() if val)
                        
                        if score_new > score_ex:
                            unique_voters[s_no] = v
                        # Else keep existing
                    else:
                        unique_voters[s_no] = v
                
                all_voters = list(unique_voters.values())
                logging.info(f"Deduplicated to {len(all_voters)} unique voters.")
            
            # 4. Sort by Serial Number
            if all_voters:
                from src.utils import bengali_to_int
                all_voters.sort(key=lambda x: bengali_to_int(x.get('serial_no', '')))
                logging.info(f"Sorted {len(all_voters)} voters by serial number.")

        except Exception as e:
            logging.error(f"Error processing PDF: {e}")
            raise

        return all_voters

    def _extract_text_from_page(self, pdf, page_index):
        """
        Returns raw text from a page (via Text Layer or OCR).
        """
        page = pdf.pages[page_index]
        
        # Strategy 1: Text Extraction (pdfplumber)
        if not self.use_ocr:
            text = page.extract_text()
            if text and len(text) > 50:
                logging.info(f"Page {page_index + 1}: Text layer detected.")
                return text
            else:
                logging.warning(f"Page {page_index + 1}: No text layer found or text too short. Switching to OCR.")
        
        # Strategy 2: OCR
        # For OCR we rely on external image conversion, so we don't use the `page` object from pdfplumber directly
        # but rather the file path + index.
        return self._extract_text_ocr(page_index)

    def _extract_text_ocr(self, page_index):
        """
        Convert page to image and run OCR, returning just the text string.
        """
        # Hardcoded path based on system search
        poppler_path = r"C:\poppler-25.12.0\Library\bin"
        
        try:
            logging.info(f"Converting page {page_index + 1} to image...")
            # Boost DPI to 350 (from default 200) to help separate columns
            images = convert_from_path(self.file_path, first_page=page_index+1, last_page=page_index+1, poppler_path=poppler_path, dpi=350)
            
            if not images:
                return ""
                
            target_image = images[0]
            
            # DEBUG: Save image to check quality
            # target_image.save(f"debug_page_{page_index + 1}_full.png")
            
            # Strategy: Split into columns to prevent merging
            # Standard voter list is 3 columns usually.
            # We will split into 3 vertical strips with small overlap.
            
            width, height = target_image.size
            # 3 columns approx.
            col_width = width // 3
            overlap = 50 # pixels overlap to be safe
            
            # Crop 1: Left
            left_box = (0, 0, col_width + overlap, height)
            
            # Crop 2: Middle
            # Center around width/2? 
            # col1_end = col_width
            # col2_start = col_width
            # Let's just do mathematical 3 strips.
            
            # Smart Split: 0-36%, 30-66%, 63-100%?
            
            # Crops with generous overlap
            # Left: 0 - 45%
            # Mid: 25% - 75%
            # Right: 55% - 100%
            
            # Image 1 (Left)
            img1 = target_image.crop((0, 0, int(width * 0.45), height))
            
            # Image 2 (Middle)
            img2 = target_image.crop((int(width * 0.25), 0, int(width * 0.75), height))
            
            # Image 3 (Right)
            img3 = target_image.crop((int(width * 0.55), 0, width, height))
            
            full_text = ""
            
            logging.info(f"Splitting page {page_index + 1} into 3 columns for OCR...")
            
            for i, chunk_img in enumerate([img1, img2, img3]):
                # PSM 6 = Assume a single uniform block of text. 
                # This helps prevent Tesseract from dropping "header" lines like '0006 Name...' 
                # that might look like captions or noise in PSM 3.
                chunk_text = pytesseract.image_to_string(chunk_img, lang='ben', config='--psm 6')
                full_text += f"\n{chunk_text}\n"
            
            return full_text
            
        except Exception as e:
            logging.error(f"OCR failed for page {page_index + 1}: {e}")
            return ""


    def _process_page_ocr(self, page_index):
        """
        Convert page to image and run OCR.
        Note: Requires poppler installed for pdf2image and tesseract installed.
        """
        # Hardcoded path based on system search
        poppler_path = r"C:\poppler-25.12.0\Library\bin"
        
        try:
            logging.info(f"Converting page {page_index + 1} to image...")
            images = convert_from_path(self.file_path, first_page=page_index+1, last_page=page_index+1, poppler_path=poppler_path)
            
            if not images:
                logging.warning(f"No images generated for page {page_index + 1}")
                return []
                
            # Assuming one image per page
            target_image = images[0]
            
            # DEBUG: Save image to check quality
            debug_img_path = f"debug_page_{page_index + 1}.png"
            target_image.save(debug_img_path)
            logging.info(f"Saved debug image to {debug_img_path}")
            
            logging.info(f"Running OCR on page {page_index + 1}...")
            text = pytesseract.image_to_string(target_image, lang='ben')
            
            return self.parser.parse_text_page(text)
            
        except Exception as e:
            logging.error(f"OCR failed for page {page_index + 1}: {e}")
            return []

