FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY services/api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY services/api /app
RUN chmod +x /app/start.sh

ENV DB_URL=sqlite:///./dev.db

EXPOSE 8000

CMD ["/app/start.sh"]
