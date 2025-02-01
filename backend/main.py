from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import asyncio
import io
import PyPDF2
from PIL import Image
import pytesseract
from backend.services.openai_service import generate_chat_response, generate_extraction_prompt

class ChatMessage(BaseModel):
    content: str
    role: str
    file: Optional[dict] = None

app = FastAPI(title="BluService", description="Backend service for BluDoc Integration Demo App")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except:
        active_connections.remove(websocket)

async def extract_text_from_pdf(content: bytes) -> str:
    """
    Extract text content from a PDF file
    """
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

async def extract_text_from_image(content: bytes) -> str:
    """
    Extract text content from an image using OCR
    """
    try:
        # Open image using PIL
        image = Image.open(io.BytesIO(content))
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from image: {str(e)}")

@app.post("/chat")
async def chat_with_llm(message: ChatMessage):
    """
    Chat with the LLM
    """
    try:
        # If there's a file, process it first
        if message.file:
            file_content = message.file.get("content", "")
            file_type = message.file.get("type", "")
            
            if file_type.startswith('image/'):
                document_text = await extract_text_from_image(file_content)
            elif file_type == 'application/pdf':
                document_text = await extract_text_from_pdf(file_content)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file format. Please upload a PDF or image file."
                )
            
            # Generate extraction prompt for the document
            prompt = await generate_extraction_prompt(
                document_content=document_text,
                instruction_text=message.content
            )
            
            # Use the generated prompt as context for the chat
            context = f"Document content: {document_text}\nGenerated prompt: {prompt}"
            user_message = f"{message.content}\nPlease analyze this based on the document provided."
        else:
            # Regular chat without document
            context = ""
            user_message = message.content

        # Generate chat response
        response = await generate_chat_response(
            user_message=user_message,
            context=context
        )

        return {
            "response": response
        }

    except Exception as e:
        # Notify connected clients about errors only
        for connection in active_connections:
            await connection.send_json({
                "status": "error",
                "message": str(e)
            })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process_document_with_instruction(
    file: UploadFile = File(...),
    instruction_text: str = Form(...)
):
    """
    Process document with transcribed instruction in a single call
    """
    try:
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file.filename.lower().endswith('.pdf'):
            document_text = await extract_text_from_pdf(content)
        elif file.content_type.startswith('image/'):
            document_text = await extract_text_from_image(content)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload a PDF or image file."
            )
        
        # Generate extraction prompt using GPT-4
        prompt = await generate_extraction_prompt(
            document_content=document_text,
            instruction_text=instruction_text
        )
        
        # Notify connected clients about the progress
        for connection in active_connections:
            await connection.send_json({
                "status": "success",
                "message": "Prompt generated successfully"
            })
        
        return {
            "message": "Processing completed successfully",
            "generated_prompt": prompt
        }
    except Exception as e:
        # Notify connected clients about the error
        for connection in active_connections:
            await connection.send_json({
                "status": "error",
                "message": str(e)
            })
        raise HTTPException(status_code=500, detail=str(e)) 