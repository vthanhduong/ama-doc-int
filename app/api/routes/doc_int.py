from fastapi import APIRouter, UploadFile, File
from app.core.config import settings
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from io import BytesIO


router = APIRouter(prefix="/doc-int", tags=["Document Analyzation"])

@router.post('/analyze')
async def analyze_document(document: UploadFile = File(...)):
    '''
    Analyze uploaded document for result
    '''
    endpoint = settings.AZURE_RESOURCE_ENDPOINT
    api_key = settings.AZURE_RESOURCE_API_KEY
    
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
    rwResult = {
        "content": result.content,
        "paragraphs": result.paragraphs,
        "tables": result.tables,
        "sections": result.sections
    }
    return rwResult