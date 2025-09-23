FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="${PYTHONPATH}:/app"

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "crypto_mcp_server:sse_app"]
