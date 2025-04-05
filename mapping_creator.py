import requests
from PyPDF2 import PdfReader
from io import BytesIO
from database import Session, LegalSection, SectionMapping
from datetime import datetime
import re
import time
from difflib import SequenceMatcher

def download_pdf_to_text(url):
    """Download PDF and extract text with error handling"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        with BytesIO(response.content) as pdf_file:
            reader = PdfReader(pdf_file)
            return "\n".join(page.extract_text() for page in reader.pages)
    except Exception as e:
        print(f"PDF Download Error: {str(e)}")
        return None

def extract_sections(text, code_type):
    """Improved section extraction with code-specific rules"""
    sections = []
    current_section = None
    
    # Common patterns for both codes
    patterns = {
        'IPC': r'^(?:Section\s*)?(\d+[A-Z]*)[\.\:\s]*(.*)',
        'BNS': r'^(\d+[A-Z]*)[\.\:\-\s]*(.*)'
    }
    
    for line in text.split('\n'):
        line = line.strip()
        match = re.match(patterns[code_type], line)
        if match:
            if current_section:
                sections.append(current_section)
            current_section = (match.group(1), match.group(2).strip(), "")
        elif current_section:
            num, title, content = current_section
            current_section = (num, title, content + "\n" + line)
    
    if current_section:
        sections.append(current_section)
    return sections

def text_similarity(text1, text2):
    """Calculate similarity score between two texts (0-1)"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def create_mappings():
    """Main function to create IPC-BNS mappings"""
    db_session = Session()
    
    # PDF URLs (official sources)
    pdf_urls = {
        'IPC':"https://www.indiacode.nic.in/bitstream/123456789/15289/1/ipc_act.pdf",
        'BNS':"https://www.indiacode.nic.in/bitstream/123456789/20062/1/a2023-45.pdf"
    }
    
    # 1. Download and parse both codes
    for code_type, url in pdf_urls.items():
        print(f"Processing {code_type}...")
        pdf_text = download_pdf_to_text(url)
        if not pdf_text:
            continue
            
        sections = extract_sections(pdf_text, code_type)
        for num, title, text in sections:
            if not db_session.query(LegalSection).filter_by(
                code_type=code_type, 
                section_number=num
            ).first():
                db_session.add(LegalSection(
                    code_type=code_type,
                    section_number=num,
                    section_title=title,
                    full_text=text,
                    effective_date=datetime(1860,1,1) if code_type=='IPC' else datetime(2024,7,1)
                ))
        db_session.commit()
    
    # 2. Create mappings
    print("Creating mappings...")
    ipc_sections = db_session.query(LegalSection).filter_by(code_type='IPC').all()
    bns_sections = db_session.query(LegalSection).filter_by(code_type='BNS').all()
    
    for ipc in ipc_sections:
        best_match = None
        best_score = 0
        
        for bns in bns_sections:
            # Compare both titles and content
            title_score = text_similarity(ipc.section_title, bns.section_title)
            content_score = text_similarity(ipc.full_text, bns.full_text)
            combined_score = (title_score * 0.4) + (content_score * 0.6)
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = bns
        
        if best_match and best_score > 0.6:  # Minimum similarity threshold
            mapping_type = 'direct' if best_score > 0.85 else 'modified'
            
            if not db_session.query(SectionMapping).filter_by(
                ipc_section_id=ipc.id,
                bns_section_id=best_match.id
            ).first():
                db_session.add(SectionMapping(
                    ipc_section_id=ipc.id,
                    bns_section_id=best_match.id,
                    confidence=int(best_score * 100),
                    mapping_type=mapping_type,
                    notes=f"Automatically mapped with score {best_score:.2f}"
                ))
    
    db_session.commit()
    print("Mapping completed!")

def print_mappings():
    """Display the created mappings"""
    db_session = Session()
    mappings = db_session.query(
        SectionMapping,
        LegalSection.section_number.label('ipc_num'),
        LegalSection.section_title.label('ipc_title'),
        SectionMapping.section_number.label('bns_num'),
        SectionMapping.section_title.label('bns_title')
    ).join(
        LegalSection, SectionMapping.ipc_section_id == LegalSection.id
    ).join(
        LegalSection.alias('bns_section'), SectionMapping.bns_section_id == SectionMapping.id
    ).all()
    
    print("\nIPC to BNS Mappings:")
    for map, ipc_num, ipc_title, bns_num, bns_title in mappings:
        print(f"IPC {ipc_num} ({ipc_title[:30]}...) → BNS {bns_num} ({bns_title[:30]}...)")
        print(f"  Type: {map.mapping_type}, Confidence: {map.confidence}%")
        print("-" * 80)

if __name__ == "__main__":
    create_mappings()
    print_mappings()