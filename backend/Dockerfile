FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Stockfish
RUN wget -q -O /tmp/stockfish.zip https://github.com/official-stockfish/Stockfish/releases/download/sf_15.1/stockfish_15.1_linux_x64_avx2.zip \
    && mkdir -p /opt/stockfish \
    && unzip -q /tmp/stockfish.zip -d /opt/stockfish \
    && mv /opt/stockfish/stockfish* /usr/local/bin/stockfish || true

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]