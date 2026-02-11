FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["sh", "-c", "python scripts/run_api.py --config config/example.yaml --host 0.0.0.0 --port ${PORT:-8080}"]
