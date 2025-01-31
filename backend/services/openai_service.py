import openai
import os
from dotenv import load_dotenv
load_dotenv()

# Set the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

async def generate_extraction_prompt(document_content: str, instruction_text: str) -> str:
    """
    Generate extraction prompt using GPT-4
    """
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at creating extraction prompts for document processing."
                },
                {
                    "role": "user",
                    "content": (
                        f"Create an extraction prompt for the following document content: {document_content}\n"
                        f"Based on these instructions: {instruction_text}"
                    )
                }
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        raise Exception(f"Error generating prompt: {str(e)}") 