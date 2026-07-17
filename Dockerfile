# Stage 1: Builder
FROM python:3.11-slim AS builder
RUN pip install --upgrade pip setuptools
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final production image
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
RUN pip install --upgrade pip setuptools
COPY . .
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
EXPOSE 10000
RUN useradd --create-home appuser
RUN chown -R appuser:appuser /app
RUN chmod -R u+rwX /app
USER appuser
CMD ["python", "app.py"]
