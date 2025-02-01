from typing import Dict, List, Optional, Union, AsyncGenerator
from smolagents import CodeAgent, ToolCallingAgent, Tool, LiteLLMModel
from smolagents.memory import ActionStep
from pydantic import BaseModel
import asyncio

class AgentConfig(BaseModel):
    """Configuration for BluApp agents"""
    model_name: str = "gpt-4"
    api_key: str 
    max_steps: int = 6
    planning_interval: Optional[int] = None
    verbosity_level: int = 1
    
    model_config = {
        'protected_namespaces': ()  # This fixes the warning
    }

class BluAppAgent:
    """
    Main agent class for BluApp that wraps smolagents functionality.
    Handles both chat and document processing workflows.
    """
    def __init__(
        self,
        config: AgentConfig,
        tools: List[Tool],
        use_code_agent: bool = False
    ):
        self.config = config
        self.tools = tools
        
        # Initialize model
        self.model = LiteLLMModel(
            model_id=config.model_name,
            api_key=config.api_key
        )

        # Initialize base agent
        agent_class = CodeAgent if use_code_agent else ToolCallingAgent
        self.agent = agent_class(
            tools=tools,
            model=self.model,
            max_steps=config.max_steps,
            planning_interval=config.planning_interval,
            verbosity_level=config.verbosity_level
        )

        self.chat_history = []

    async def process_message(
        self, 
        message: str,
        context: Optional[Dict] = None
    ) -> AsyncGenerator[ActionStep, None]:
        """
        Process a user message through the agent.
        
        Args:
            message: The user's message
            context: Optional context like document info
            
        Yields:
            ActionStep objects as the agent processes the message
        """
        # Add context to agent state if provided
        if context:
            self.agent.state.update(context)

        # Store user message
        self.chat_history.append({
            "role": "user",
            "content": message
        })

        # Run agent in a separate thread to not block
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.agent.run, message)
        
        # Get steps from memory
        steps = self.agent.memory.steps
        
        # Yield each step
        for step in steps:
            yield step
            
        # Store final answer in chat history
        if result:
            self.chat_history.append({
                "role": "assistant",
                "content": str(result)
            })

    def get_agent_logs(self) -> List[ActionStep]:
        """Get the agent's execution logs"""
        return self.agent.memory.steps

    def clear_history(self):
        """Clear chat history"""
        self.chat_history = [] 