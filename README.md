# BluApp - AI Chat Application

## Overview
BluApp is an AI-powered chat application that combines document analysis capabilities with natural conversation. It features a modern, responsive interface with dark mode support and real-time file processing.

## Features
- Real-time chat with GPT-4
- Document analysis (PDF and Images)
- Voice input support
- Dark/Light theme switching
- File upload with preview
- Real-time WebSocket notifications
- Responsive design with Tailwind CSS
- Markdown rendering support

## Project Structure
```
blu/
├── backend/             # FastAPI backend
│   ├── main.py         # Main FastAPI application
│   ├── services/       # Backend services
│   │   ├── openai_service.py  # OpenAI integration
│   │   └── ...
│   └── ...
│
└── frontend/           # React frontend
    ├── src/           
    │   ├── App.tsx    # Main application component
    │   ├── contexts/  # React contexts (theme, etc.)
    │   └── ...
    └── ...
```

## Technical Stack
### Backend
- FastAPI
- Python 3.8+
- OpenAI GPT-4
- PyTesseract (OCR)
- WebSockets
- PDF Processing (PyPDF2)

### Frontend
- React with TypeScript
- Tailwind CSS
- Heroicons
- WebSocket client
- @tailwindcss/typography

## Setup

### Backend
1. Create and activate virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR:
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

4. Create .env file and set:
```
OPENAI_API_KEY=your_api_key_here
```

5. Run the backend:
```bash
uvicorn backend.main:app --reload --port 8080
```

### Frontend
1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run the frontend:
```bash
npm run dev
```

## Development
- Backend API runs on: http://localhost:8080
- Frontend dev server runs on: http://localhost:5173
- WebSocket connection: ws://localhost:5173/ws

## Features in Detail

### Chat Interface
- Real-time messaging with GPT-4
- Markdown support for responses
- Message history with user/assistant distinction
- Auto-scrolling to latest messages

### File Processing
- Support for PDF and image files
- OCR for image text extraction
- PDF text extraction
- File preview thumbnails
- File size and type display

### Theme Support
- System-preference based default theme
- Manual theme switching
- Persistent theme preference
- Dark mode optimized UI

### Voice Input (WIP)
- Voice recording capability
- Audio to text conversion
- Real-time recording status

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 