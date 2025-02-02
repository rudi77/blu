from openai import AsyncOpenAI
import json
from typing import Dict, Optional
from ..telemetry.openai_metrics import trace_openai_request

# Define function definitions to be passed to the Chat API.
# Here we define a function "analyze_document" that can be called by the model.
FUNCTION_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_document",
            "description": "Analyze the provided document content with a given instruction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_content": {
                        "type": "string",
                        "description": "The full text content of the document."
                    },
                    "instruction": {
                        "type": "string",
                        "description": "Instruction on what to analyze from the document."
                    }
                },
                "required": ["doc_content", "instruction"],
            },
        }
    },
]

async def analyze_document_func(doc_content: str, instruction: str) -> str:
    """
    Local implementation of the analyze_document function.
    In production, you might call BluDeltaService or perform more advanced processing.
    For demo, we return a dummy analysis.
    """
    return f"Analyzed document based on instruction: '{instruction}'. Document excerpt: {doc_content[:100]}..."

class OpenAIAgent:
    def __init__(self, model_name: str, api_key: str, system_prompt: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        # Initialize the async client from OpenAI's new API
        self.async_client = AsyncOpenAI(api_key=api_key)
        self.system_prompt = system_prompt or "You are a helpful assistant."
    
    @trace_openai_request
    async def _call_openai(self, messages, **kwargs):
        """Make an OpenAI API call with telemetry."""
        return await self.async_client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=FUNCTION_DEFINITIONS,
            tool_choice="auto",
            **kwargs
        )
    
    async def get_completion(self, messages, **kwargs):
        """Get a completion from OpenAI with telemetry."""
        try:
            response = await self._call_openai(messages, **kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting completion: {str(e)}")
            raise
    
    async def process_message(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Process a user message using OpenAI's ChatCompletion API with function calling.
        """
        # Build the conversation messages.
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # If the context includes document information, add it as a system message.
        if context and "document" in context:
            doc = context["document"]
            messages.append({
                "role": "system",
                "content": f"Document information: {doc.get('text', '')}"
            })
        
        # Append the user message.
        messages.append({"role": "user", "content": message})
        
        # Call OpenAI ChatCompletion with function calling enabled.
        response = await self.async_client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=FUNCTION_DEFINITIONS,
            tool_choice="auto"
        )
        
        message_obj = response.choices[0].message

        # Check if the model wants to call a tool
        if message_obj.tool_calls:
            tool_call = message_obj.tool_calls[0]
            tool_name = tool_call.function.name
            
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except Exception:
                tool_args = {}
            
            if tool_name == "analyze_document":
                doc_content = tool_args.get("doc_content", "")
                instruction = tool_args.get("instruction", "")
                # Execute the local function.
                func_result = await analyze_document_func(doc_content, instruction)
                
                # Add the function call message and its result to the conversation.
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_args)
                            }
                        }
                    ]
                })
                messages.append({
                    "role": "tool",
                    "content": func_result,
                    "tool_call_id": tool_call.id
                })
                
                # Re-call the API to get the final answer.
                second_response = await self.async_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages
                )
                return second_response.choices[0].message.content or ""
            else:
                return f"Unknown tool call: {tool_name}"
        else:
            # No tool was called. Return the assistant's reply.
            return message_obj.content or "" 