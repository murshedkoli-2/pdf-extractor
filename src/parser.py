import re
import logging

class VoterParser:
    def __init__(self):
        # Patterns
        # Improved split pattern: 
        # 1. Allow 2-5 digits for serial (sometimes OCR adds noise)
        # 2. Allow period (.) or Bengali Pipe (|) or just space
        # 3. Allow missing serial entirely if "নাম:" is strong, BUT "মাতার নাম" or "পিতার নাম" contains "নাম".
        #    So we must ensure it's "Start of Line" or "Serial + Name".
        #    Typically "Name:" starts a line or follows a large gap.
        
        # Strategy: Look for "Serial. Name" OR just "Name:" if it's not preceded by "Father/Mother"
        # Since looking behind is hard in variable width, we stick to finding "Name:" 
        # and checking if it's "Father's Name".
        # But "Father's Name" is "পিতার নাম". distinct from "নাম".
        
        # Regex:
        # (group 1: Serial optional) 'নাম:'
        self.split_pattern = re.compile(r'(?:^|\n|\s{2,})(?:([০-৯]{2,5})[.|।]?\s*)?নাম[:\s]+')
        
        # Field patterns (Updated keys will be handled in _parse_single_voter)
        self.p_name = re.compile(r'^(.*?)(?=\n|ভোটার|পিতা|স্বামী|মাতা)', re.DOTALL) # Name is immediate after split
        self.p_voter_no = re.compile(r'ভোটার নং[:\s.।]+([০-৯]+)') # Handle . or | chars in separator
        self.p_father = re.compile(r'(?:পিতা|স্বামী)[:\s.।]+(.*?)(?=\n|মাতা)', re.DOTALL)
        self.p_mother = re.compile(r'মাতা[:\s.।]+(.*?)(?=\n|পেশা)', re.DOTALL)
        self.p_occupation = re.compile(r'পেশা[:\s.।]+(.*?)(?=জন্ম তারিখ|\n)', re.DOTALL)
        self.p_dob = re.compile(r'জন্ম তারিখ[:\s.।]+([০-৯/]+)')
        self.p_address = re.compile(r'ঠিকানা[:\s.।]+(.*?)(?=$|\n(?:[০-৯]{2,5}[.|।]?)?\s*নাম|  \d)', re.DOTALL)

        # Metadata patterns (for Page 1)
        self.p_district = re.compile(r'জেলা[:\s]+(.*?)(?=\n)', re.DOTALL)
        self.p_upazila = re.compile(r'উপজেলা/থানা[:\s]+(.*?)(?=\n|সিটি)', re.DOTALL)
        self.p_union = re.compile(r'ইউনিয়ন/.*?[:\s]+(.*?)(?=\n|ক্যান্টনমেন্ট)', re.DOTALL)
        self.p_ward = re.compile(r'ওয়ার্ড নম্বর.*?[:\s]+([০-৯]+)')
        self.p_area = re.compile(r'ভোটার এলাকা[:\s]+(.*?)(?=\n|সিটি|সর্বমোট)', re.DOTALL)
        self.p_area_code = re.compile(r'ভোটার এলাকার নম্বর[:\s]+([০-৯]+)')

    def parse_header_page(self, text):
        """
        Parses metadata from the header/cover page.
        """
        logging.info(f"Header Page Text Dump:\n{text}")
        meta = {}
        # Simple cleanup
        text = text.replace('\r', '')

        m_dist = self.p_district.search(text)
        if m_dist: meta['district'] = m_dist.group(1).strip()
        
        m_upz = self.p_upazila.search(text)
        if m_upz: meta['upazila'] = m_upz.group(1).strip()
        
        m_union = self.p_union.search(text)
        if m_union: meta['union'] = m_union.group(1).strip()
        
        m_ward = self.p_ward.search(text)
        if m_ward: meta['ward_number'] = m_ward.group(1).strip()
        
        m_area = self.p_area.search(text)
        if m_area: meta['voter_area'] = m_area.group(1).strip()
        
        m_acose = self.p_area_code.search(text)
        if m_acose: meta['voter_area_code'] = m_acose.group(1).strip()
        
        return meta

    def parse_text_page(self, text, global_meta=None):
        """
        Parses raw text from a page and returns a list of voter objects.
        """
        voters = []
        # logging.info(f"Raw Text Sample (First 500 chars):\n{text[:500]}...") # Too noisy
        
        matches = list(self.split_pattern.finditer(text))
        if not matches:
             # logging.warning("No voter blocks found on this page.")
             return []

        for i, match in enumerate(matches):
            entries = global_meta.copy() if global_meta else {}
            
            # Group 1 is serial no (if present)
            if match.group(1):
                entries['serial_no'] = match.group(1)
            else:
                entries['serial_no'] = "" # Missing or not captured
            
            # block starts *after* the "Name:" label because split_pattern consumes it?
            # NO, finditer returns the match object for the pattern.
            # Use match.end() as the start of the content (The name value itself).
            
            block_start = match.end()
            if i < len(matches) - 1:
                block_end = matches[i+1].start()
            else:
                block_end = len(text)
            
            block_text = text[block_start:block_end]
            
            # IMPORTANT: Since "Name:" is consumed, the block_text starts with the Actual Name.
            # We need to prepend "Name: " so our `_parse_single_voter` (which expects "Name:") works?
            # OR we modify `_parse_single_voter` to treat the start of text as Name.
            # Modified `p_name` to `^(.*?)` helps here.
            
            voter = self._parse_single_voter(block_text, entries)
            if voter:
                voters.append(voter)
        
        return voters

    def _parse_single_voter(self, block_text, entries):
        """
        Extracts fields from a single voter block text.
        """
        # Clean text
        block_text = block_text.strip()
        
        # 1. Name (It's at the start now, since we split by 'Name:')
        m_name = self.p_name.match(block_text)
        if m_name:
            entries['name'] = m_name.group(1).strip()
        
        # 2. Voter ID
        m_vno = self.p_voter_no.search(block_text)
        if m_vno:
            entries['voter_id'] = m_vno.group(1).strip()

        # 3. Father/Husband Name
        m_father = self.p_father.search(block_text)
        if m_father:
            entries['father_name'] = m_father.group(1).strip()
        else:
            entries['father_name'] = ""

        # 4. Mother Name
        m_mother = self.p_mother.search(block_text)
        if m_mother:
            entries['mother_name'] = m_mother.group(1).strip()
        else:
            entries['mother_name'] = ""
            
        # 5. Occupation
        m_occ = self.p_occupation.search(block_text)
        if m_occ:
            entries['occupation'] = m_occ.group(1).strip()
            
        # 6. Date of Birth
        m_dob = self.p_dob.search(block_text)
        if m_dob:
            entries['date_of_birth'] = m_dob.group(1).strip()
            
        # 7. Address
        m_addr = self.p_address.search(block_text)
        if m_addr:
            entries['address'] = m_addr.group(1).strip()
            
        # Basic validation: Must have Name or Voter ID to be valid
        if not entries.get('name') and not entries.get('voter_id'):
            return None
            
        return entries
