FROM python:3.12-slim

WORKDIR /app

# System deps needed for asyncpg / psycopg build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Runs migrations before starting so a fresh deploy (e.g. on Render) always
# has an up-to-date schema. $PORT is set by hosting platforms like Render;
# falls back to 8000 for plain `docker run`.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
