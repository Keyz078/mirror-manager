FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libffi-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

VOLUME ["/mirror"]

COPY . .

EXPOSE 5000

CMD ["python", "main.py", "--config", "config/config.json"]