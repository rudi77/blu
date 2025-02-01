from typing import Dict, List, Optional, Union
from smolagents import CodeAgent, ToolCallingAgent, Tool, LiteLLMModel
from smolagents.memory import ActionStep
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """Configuration for BluApp agents"""
    model_name: str = "gpt-4"
    api_key: str 
    max_steps: int = 6
    planning_interval: Optional[int] = None
    verbosity_level: int = 1

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
    ) -> Union[str, Dict]:
        """
        Process a user message through the agent.
        
        Args:
            message: The user's message
            context: Optional context like document info
            
        Returns:
            Agent response (str) or processed result (dict)
        """
        # Add context to agent state if provided
        if context:
            self.agent.state.update(context)

        # Run agent
        result = self.agent.run(message)
        
        # Store in chat history
        self.chat_history.append({
            "role": "user",
            "content": message
        })
        self.chat_history.append({
            "role": "assistant", 
            "content": str(result)
        })

        return result

    def get_agent_logs(self) -> List[ActionStep]:
        """Get the agent's execution logs"""
        return self.agent.memory.steps

    def clear_history(self):
        """Clear chat history"""
        self.chat_history = [] 