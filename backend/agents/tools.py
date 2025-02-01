from typing import Optional, Dict
from smolagents import tool
from ..services.bludelta_service import BluDeltaService
from ..database.prompt_store import PromptStore

bludelta_service = BluDeltaService()
prompt_store = PromptStore()

@tool
async def generate_prompt(doc_type: str, context: Optional[Dict] = None) -> str:
    """
    Generate a custom prompt for a specific document type.
    
    Args:
        doc_type: Type of document (e.g. invoice, receipt, contract)
        context: Optional additional context about the document
    """
    # First check if we have a stored prompt for this type
    stored_prompt = await prompt_store.get_prompt(doc_type)
    if stored_prompt:
        if context:
            return stored_prompt.format(**context)
        return stored_prompt
        
    # Generate new prompt if none exists
    base_prompt = f"You are analyzing a {doc_type}. Extract all relevant information."
    if context:
        base_prompt += f"\nAdditional context: {context}"
    return base_prompt

@tool 
async def analyze_document(doc_id: str, prompt: str) -> Dict:
    """
    Send document to BluDeltaService for analysis.
    
    Args:
        doc_id: ID of uploaded document
        prompt: Custom prompt to use for analysis
    """
    return await bludelta_service.analyze_document(doc_id, prompt)

@tool
async def store_prompt(doc_type: str, prompt: str) -> bool:
    """
    Store a generated prompt in the prompt store.
    
    Args:
        doc_type: Type of document
        prompt: The prompt to store
    """
    return await prompt_store.store_prompt(doc_type, prompt) 