FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 8501

# Default: run FastAPI backend
CMD ["uvicorn", "src.tool.api:app", "--host", "0.0.0.0", "--port", "8000"]
