# BluDoc Integration Demo

## Project Structure
```
blu/
├── backend/             # FastAPI backend
│   ├── main.py         # Main FastAPI application
│   ├── services/       # Backend services
│   └── ...
│
└── frontend/           # React frontend
    ├── src/            # Frontend source code
    └── ...
```

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

3. Create .env file and set required environment variables

4. Run the backend:
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