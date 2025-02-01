from typing import List, Optional
from enum import Enum
from .base import BluAppAgent, AgentConfig
from .tools import generate_prompt, analyze_document, store_prompt
from smolagents import Tool

class AgentType(Enum):
    CHAT = "chat"
    DOCUMENT = "document"

def create_agent(
    agent_type: AgentType,
    config: AgentConfig,
    additional_tools: Optional[List[Tool]] = None
) -> BluAppAgent:
    """
    Create an agent instance based on type.
    
    Args:
        agent_type: Type of agent to create
        config: Agent configuration
        additional_tools: Optional additional tools to add
    """
    base_tools = []
    
    if agent_type == AgentType.DOCUMENT:
        # Document processing agent needs document-specific tools
        base_tools.extend([
            generate_prompt,
            analyze_document, 
            store_prompt
        ])
        use_code_agent = True
    else:
        # Chat agent just needs basic conversation
        use_code_agent = False
        
    if additional_tools:
        base_tools.extend(additional_tools)
        
    return BluAppAgent(
        config=config,
        tools=base_tools,
        use_code_agent=use_code_agent
    ) 