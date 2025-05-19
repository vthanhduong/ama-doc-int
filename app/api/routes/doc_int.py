from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import settings
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from io import BytesIO
import json


router = APIRouter(prefix="/doc-int", tags=["Document Analyzation"])

def getIndex(str):
    p = str.split("/")
    return int(p[-1])

def getType(str):
    p = str.split("/")
    return p[1]

def find_referenced_section_indices(sections):
    """
    Trả về tập hợp các index của section con (bị tham chiếu bên trong các section khác)
    """
    referenced = set()
    for section in sections:
        for e in section.get('elements', []):
            if getType(e) == 'sections':
                referenced.add(getIndex(e))
    return referenced

def process_table(table):
    r_table = {
        'rowCount': table['rowCount'],
        'columnCount': table['columnCount'],
        'cells': []
    }
    for cell in table['cells']:
        c_cell = {
            'kind': cell.get('kind'),
            'rowIndex': cell.get('rowIndex'),
            'columnIndex': cell.get('columnIndex'),
            'columnSpan': cell.get('columnSpan'),
            'rowSpan': cell.get('rowSpan'),
            'content': cell.get('content'),
        }
        c_cell = {k: v for k, v in c_cell.items() if v not in [None, '', []]}
        r_table['cells'].append(c_cell)
    return r_table

def process_response(sections, section, paragraphs, tables):
    elemSection = {
        'content': '',
        'paragraphs': [],
        'sections': [],
        'tables': []
    }
    for e in section['elements']:
        e_type = getType(e)
        e_index = getIndex(e)
        if e_type == 'sections':
            child_sections = process_response(sections, sections[e_index], paragraphs, tables)
            elemSection['sections'].append(child_sections)
        if e_type == 'paragraphs':
            par = paragraphs[e_index]
            elemSection['paragraphs'].append(par['content'])
            if 'role' in par and par['role'] == 'sectionHeading':
                elemSection['content'] = par['content']
        if e_type == 'tables':
            tab = process_table(tables[e_index])
            elemSection['tables'].append(tab)
    elemSection = {k: v for k, v in elemSection.items() if v not in [None, '', []]}
    return elemSection


@router.post('/analyze')
async def analyze_document(document: UploadFile = File(...)):
    '''
    Analyze uploaded document for result
    '''
    endpoint = settings.AZURE_RESOURCE_ENDPOINT
    api_key = settings.AZURE_RESOURCE_API_KEY
    
    try:
        contents = await document.read()
        file_stream = BytesIO(contents)
        
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-layout",
            file_stream
        )
        result = poller.result()
        
        paragraphs = result['paragraphs']
        tables = result['tables']
        sections = result['sections']
        content = result['content']
        result = {
            'content': content,
            'paragraphs':  [p['content'] for p in paragraphs]
        }
        referenced_indices = find_referenced_section_indices(sections)
        root_sections = [s for i, s in enumerate(sections) if i not in referenced_indices]
        
        customSections = []
        for s in root_sections:
            customSections.append(process_response(sections, s, paragraphs, tables))
        result['sections'] = customSections
        return result
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

@router.post('/analyze-test')
async def analyze_document_for_testing():
    '''
    Analyze json file and then respond in json structure
    '''
    try:
        with open('app/api/routes/response.json', encoding="utf8") as f:
            jsonObject = json.load(f)
        paragraphs = jsonObject['paragraphs']
        tables = jsonObject['tables']
        sections = jsonObject['sections']
        content = jsonObject['content']
        result = {
            'content': content,
            'paragraphs': [p['content'] for p in paragraphs]
        }
        referenced_indices = find_referenced_section_indices(sections)
        root_sections = [s for i, s in enumerate(sections) if i not in referenced_indices]
        
        customSections = []
        for s in root_sections:
            customSections.append(process_response(sections, s, paragraphs, tables))
        result['sections'] = customSections
        return result
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))