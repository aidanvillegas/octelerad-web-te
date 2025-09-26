FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY services/api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY services/api /app

ENV DB_URL=sqlite:///./dev.db

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
