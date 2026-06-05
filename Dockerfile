FROM python:3.12-slim

WORKDIR /app

# Install deps first for better layer caching
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code and the frontend it serves (layout mirrors the repo,
# so app.main's FRONTEND_DIR (../../frontend) resolves correctly).
COPY backend ./backend
COPY frontend ./frontend

WORKDIR /app/backend

# Railway/Render inject $PORT at runtime
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
