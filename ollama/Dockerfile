FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://ollama.com/install.sh | sh

COPY . /app

EXPOSE 11434

USER root

RUN chmod +x /app/start.sh

CMD ["sh", "/app/start.sh"]
