from typing import List, Optional
from enum import Enum
from .base import BluAppAgent, AgentConfig
from .tools import generate_prompt, analyze_document, store_prompt
from smolagents import Tool

class AgentType(Enum):
    CHAT = "chat"  # Only one type needed now

def create_agent(
    agent_type: AgentType,
    config: AgentConfig,
    additional_tools: Optional[List[Tool]] = None
) -> BluAppAgent:
    """Create an agent with all available tools"""
    
    # Include all tools by default
    base_tools = [
        generate_prompt,
        analyze_document,
        store_prompt
    ]
    
    if additional_tools:
        base_tools.extend(additional_tools)
        
    return BluAppAgent(
        config=config,
        tools=base_tools,
        use_code_agent=True  # Always use code agent for flexibility
    ) 