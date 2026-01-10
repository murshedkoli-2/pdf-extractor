from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import os

pdf_path = "sample.pdf.pdf"
poppler_path = r"C:\poppler-25.12.0\Library\bin"
page_index = 2 # Page 3 (0-indexed)

print(f"Converting Page {page_index+1}...")
images = convert_from_path(pdf_path, first_page=page_index+1, last_page=page_index+1, poppler_path=poppler_path, dpi=350)
target_image = images[0]
width, height = target_image.size
print(f"Image Size: {width}x{height}")

# Define Crops - Aggressive Overlap
# Strip 3 covers the Right Column. Let's make it start very early (40%) to ensure we catch the left edge of the column.
crops = [
    (0, 0, int(width * 0.50), height),          # Left (0-50%)
    (int(width * 0.25), 0, int(width * 0.75), height), # Middle (25-75%)
    (int(width * 0.40), 0, width, height)       # Right (40-100%) - Very wide start
]

for i, box in enumerate(crops):
    print(f"Processing Strip {i+1}: Box {box}")
    crop_img = target_image.crop(box)
    
    text = pytesseract.image_to_string(crop_img, lang='ben')
    with open(f"debug_strip_{i+1}.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Saved debug_strip_{i+1}.txt")
