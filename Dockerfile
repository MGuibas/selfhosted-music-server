FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install chromium --with-deps

COPY spotifyprivado ./spotifyprivado

ENV MUSIC_DIR=/music PYTHONUNBUFFERED=1
EXPOSE 8501

CMD ["python", "-m", "spotifyprivado", "web"]
