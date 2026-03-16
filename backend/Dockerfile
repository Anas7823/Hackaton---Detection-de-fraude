FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances système requises pour OCR / DocTR
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Le code sera monté via le volume dans docker-compose, pas besoin de COPY ici en dev