# 📄 Bengali Voter List PDF Extractor & Data Parser

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://streamlit.io/)
[![OCR & Parsing](https://img.shields.io/badge/Engine-PyPDF_|_pdfplumber-green?style=for-the-badge)](https://github.com/jsvine/pdfplumber)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

An intelligent, automated PDF text and tabular extraction utility optimized for parsing scanned and digital **Bengali Electoral Rolls & Voter Lists** into structured formats (JSON, Excel, CSV).

---

## 🌟 Key Capabilities

- **🇧🇩 Specialized Bengali Script Support**: Robust parsing algorithms specifically tuned for Bengali Unicode font ligatures and layout structures.
- **📑 Multi-Page Batch Extraction**: Handles large electoral PDF registers spanning hundreds of pages with layout analysis.
- **🖥️ Interactive Streamlit Dashboard**: Clean web UI allowing users to upload PDFs, preview parsed records in real-time, and download formatted datasets.
- **📊 Clean Field Mapping**: Extracts Voter Serial Number, Name, Father's Name, Mother's Name, Voter ID, Date of Birth, and Address.

---

## 🛠️ Technology Stack

- **Language**: Python 3.10+
- **Interface**: Streamlit Web UI
- **Extraction Core**: `pdfplumber`, `pypdf`, Regular Expressions (`re`)
- **Data Export**: Pandas (CSV, Excel), JSON

---

## 🚀 Installation & Usage

```bash
# 1. Clone repository
git clone https://github.com/murshedkoli-2/pdf-extractor.git
cd pdf-extractor

# 2. Create virtual environment
python -m venv venv
# Linux/macOS: source venv/bin/activate
# Windows: .\venv\Scripts\activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Launch Streamlit Application
streamlit run app.py
```

---

## 📄 License

Distributed under the [MIT License](LICENSE).
