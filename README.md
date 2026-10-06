# Start

Install dependencies once.

```powershell
uv pip install --system -r backend/requirements.txt
npm install --prefix frontend
```

Start the API and the screen separately. Start the API first.

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend
```

```powershell
npm run dev --prefix frontend
```

The screen is at http://127.0.0.1:5173
