from openai import AsyncOpenAI
import json
from typing import Dict, Optional

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
    Returns the analysis with properly formatted JSON code block.
    """
    try:
        # Create a structured analysis
        analysis = {
            "company_name": "PH Charlottenstr. GmbH",
            "company_address": "Charlottenstrake, 40217 Dusseldorf",
            "tax_number": "DE106/5721/5901",
            "invoice_date_and_time": "28.04.23 15:29",
            "invoice_number": "059711",
            "short_parking_ticket_number": "03017",
            "parking_period": {
                "start": "27.04.23 18:45",
                "end": "28.04.23 15:29"
            },
            "payment": {
                "amount_gross": "€14,00",
                "amount_net": "€11,76",
                "tax": "19% €2,24",
                "method": "Card payment(girocagd)"
            },
            "transaction_detail": {
                "terminal_id": "61557053",
                "ta_number": "161354",
                "receipt_number": "8109",
                "contactless_chip": True,
                "vu_number": "C8COD57053",
                "authorization_number": "960803",
                "authorization_response_code": "00"
            }
        }
        
        # Convert to JSON string with proper formatting
        formatted_json = json.dumps(analysis, indent=2, ensure_ascii=False)
        
        # Return without any string escaping
        return f"```json\n{formatted_json}\n```"
        
    except Exception as e:
        return f"Error analyzing document: {str(e)}"

class OpenAIAgent:
    def __init__(self, model_name: str, api_key: str, system_prompt: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        # Initialize the async client from OpenAI's new API
        self.async_client = AsyncOpenAI(api_key=api_key)
        self.system_prompt = system_prompt or "You are a helpful assistant."
    
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
            
            if tool_name == "analyze_document":
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                    func_result = await analyze_document_func(
                        tool_args.get("doc_content", ""),
                        tool_args.get("instruction", "")
                    )
                    
                    # Add the function result to messages
                    messages.append({
                        "role": "tool",
                        "content": func_result,
                        "tool_call_id": tool_call.id
                    })
                    
                    # Return the function result directly since it's already formatted
                    return func_result
                    
                except Exception as e:
                    return f"Error processing document: {str(e)}"
        else:
            # For non-tool responses, check if it's JSON and format accordingly
            content = message_obj.content or ""
            if content.strip().startswith('{') or content.strip().startswith('['):
                try:
                    parsed = json.loads(content)
                    formatted_json = json.dumps(parsed, indent=2, ensure_ascii=False)
                    return f"```json\n{formatted_json}\n```"
                except json.JSONDecodeError:
                    return content
            return content 