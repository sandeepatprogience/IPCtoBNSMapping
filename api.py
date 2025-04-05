from fastapi import FastAPI, HTTPException
from database import Session, LegalSection, SectionMapping
from pydantic import BaseModel

app = FastAPI()

class SectionResponse(BaseModel):
    id: int
    code_type: str
    section_number: str
    section_title: str

class MappingResponse(BaseModel):
    ipc_section: SectionResponse
    bns_section: SectionResponse
    confidence: int
    mapping_type: str

@app.get("/search")
def search_sections(q: str, limit: int = 10):
    """Basic search endpoint"""
    session = Session()
    results = session.query(LegalSection).filter(
        LegalSection.full_text.contains(q)
    ).limit(limit).all()
    return [SectionResponse(**{
        'id': r.id,
        'code_type': r.code_type,
        'section_number': r.section_number,
        'section_title': r.section_title
    }) for r in results]

@app.get("/mappings/{ipc_section}")
def get_mappings(ipc_section: str):
    """Get BNS mappings for an IPC section"""
    session = Session()
    ipc = session.query(LegalSection).filter_by(
        code_type='IPC',
        section_number=ipc_section
    ).first()
    
    if not ipc:
        raise HTTPException(status_code=404, detail="IPC section not found")
    
    mappings = session.query(SectionMapping).filter_by(
        ipc_section_id=ipc.id
    ).all()
    
    response = []
    for m in mappings:
        bns = session.query(LegalSection).get(m.bns_section_id)
        response.append(MappingResponse(
            ipc_section=SectionResponse(**{
                'id': ipc.id,
                'code_type': ipc.code_type,
                'section_number': ipc.section_number,
                'section_title': ipc.section_title
            }),
            bns_section=SectionResponse(**{
                'id': bns.id,
                'code_type': bns.code_type,
                'section_number': bns.section_number,
                'section_title': bns.section_title
            }),
            confidence=m.confidence,
            mapping_type=m.mapping_type
        ))
    
    return response