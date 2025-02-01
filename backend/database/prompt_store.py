from typing import Optional, Dict

class PromptStore:
    """Simple in-memory prompt store implementation"""
    
    def __init__(self):
        self._prompts: Dict[str, str] = {}
    
    async def store_prompt(self, doc_type: str, prompt: str) -> bool:
        """Store a prompt in memory"""
        try:
            self._prompts[doc_type] = prompt
            return True
        except Exception as e:
            print(f"Error storing prompt: {e}")
            return False
            
    async def get_prompt(self, doc_type: str) -> Optional[str]:
        """Retrieve a prompt from memory"""
        return self._prompts.get(doc_type)
    
    def clear(self):
        """Clear all stored prompts"""
        self._prompts.clear()

# Create a singleton instance
prompt_store = PromptStore()

# Export the store_prompt function for convenience
async def store_prompt(doc_type: str, prompt: str) -> bool:
    return await prompt_store.store_prompt(doc_type, prompt) 