# Imagem do susia: Python 3.12 com as dependencias do projeto.
# Por padrao sobe o servidor do LangGraph (Studio/API) na porta 2024.
# Para rodar o exemplo no terminal: docker compose run --rm susia python exemplo.py

FROM python:3.12-slim

# uv instala as dependencias bem mais rapido que o pip. Vem do PyPI, o mesmo
# registro das outras dependencias (sem depender de outro registro de imagens).
RUN pip install --no-cache-dir uv==0.8.17

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_NO_CACHE=1

WORKDIR /app

# Dependencias primeiro: a camada so e refeita quando o requirements.txt muda.
COPY requirements.txt .
RUN uv pip install -r requirements.txt

# Codigo e base do RAG. O .env NAO entra na imagem (ver .dockerignore):
# as variaveis chegam pelo docker compose (env_file).
COPY . .

# Usuario sem privilegios de root.
RUN useradd --create-home susia && mkdir -p .cache && chown -R susia:susia /app
USER susia

EXPOSE 2024

# --host 0.0.0.0: aceita conexoes de fora do container (o Studio no navegador).
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-browser", "--no-reload"]
