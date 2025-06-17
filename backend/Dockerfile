FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y curl && \
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o /usr/local/bin/cloudflared && \
    chmod +x /usr/local/bin/cloudflared

RUN apt-get install -y golang && \
    go install github.com/ddollar/forego@latest && \
    cp /root/go/bin/forego /usr/local/bin/forego

COPY ./app ./app
COPY .env .env
COPY ./Procfile ./Procfile

CMD ["forego", "start", "-r"]