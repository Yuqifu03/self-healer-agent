FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies first so image layers are cached across rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The agent may only ever touch files under PROJECT_ROOT (the sandbox).
ENV PROJECT_ROOT=/app/sandbox/example_project

CMD ["python", "main.py"]
