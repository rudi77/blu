import pytest
from ..database.prompt_store import PromptStore

@pytest.mark.asyncio
async def test_prompt_store():
    store = PromptStore()
    
    # Test storing prompt
    success = await store.store_prompt("invoice", "Analyze this invoice")
    assert success is True
    
    # Test retrieving prompt
    prompt = await store.get_prompt("invoice")
    assert prompt == "Analyze this invoice"
    
    # Test non-existent prompt
    prompt = await store.get_prompt("unknown")
    assert prompt is None
    
    # Test clearing prompts
    store.clear()
    prompt = await store.get_prompt("invoice")
    assert prompt is None 