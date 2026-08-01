FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# --timeout/--retries make this resilient to slow or unstable connections --
# PyPI downloads can otherwise hit pip's default 15s read timeout and fail
# the whole build partway through.
RUN pip install --no-cache-dir --timeout 100 --retries 5 -r requirements.txt

COPY . .
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
