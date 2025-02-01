from typing import Optional, Dict
from smolagents import tool
from ..services.bludelta_service import BluDeltaService
from ..database.prompt_store import prompt_store  # Import the singleton instance

# Create singleton instances
bludelta_service = BluDeltaService()

@tool
async def generate_prompt(doc_type: str, context: Optional[Dict] = None) -> str:
    """
    Generate a custom prompt for a specific document type.
    
    Args:
        doc_type: Type of document to generate prompt for
        context: Optional context information
    """
    # First check if we have a stored prompt
    existing_prompt = await prompt_store.get_prompt(doc_type)
    if existing_prompt:
        return existing_prompt
        
    # Generate new prompt based on document type
    base_prompt = "Please analyze the following document"
    if doc_type == "invoice":
        prompt = f"{base_prompt} and extract: date, invoice number, total amount, and line items."
    elif doc_type == "receipt":
        prompt = f"{base_prompt} and extract: date, merchant name, total amount, and items purchased."
    else:
        prompt = f"{base_prompt} and provide a detailed summary."
        
    # Store the generated prompt
    await prompt_store.store_prompt(doc_type, prompt)
    return prompt

@tool
async def analyze_document(doc_id: str, prompt: str) -> Dict:
    """
    Analyze a document using BluDelta service.
    
    Args:
        doc_id: Document ID to analyze
        prompt: Prompt to use for analysis
    """
    return await bludelta_service.analyze_document(doc_id, prompt)

@tool
async def store_prompt(doc_type: str, prompt: str) -> bool:
    """
    Store a custom prompt for future use.
    
    Args:
        doc_type: Type of document
        prompt: The prompt to store
    """
    return await prompt_store.store_prompt(doc_type, prompt) 