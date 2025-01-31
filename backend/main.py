from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import asyncio
import io
import PyPDF2
from backend.services.openai_service import generate_extraction_prompt

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
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

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
        
        # Extract text from PDF
        if file.filename.lower().endswith('.pdf'):
            document_text = await extract_text_from_pdf(content)
        else:
            # For non-PDF files, try UTF-8 decoding
            try:
                document_text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file format. Please upload a PDF or text file."
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