"""API Gateway do HelpDesk TI: o único ponto de entrada (porta 8000).

- Serve a tela (index.html, app.js, estilo.css), que continua usando os mesmos endereços.
- Encaminha cada rota para o serviço certo, olhando o primeiro trecho do caminho
  (/auth e /usuarios -> Usuários, /ativos -> Inventário, /chamados -> Chamados,
  /notificacoes -> Notificações).
- Repassa o token (cabeçalho Authorization); quem confere o token é cada serviço.
- Se um serviço estiver fora do ar, responde 503 com uma mensagem clara.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from app.config import ROTAS, SERVICOS, TIMEOUT_SEGUNDOS
from app.seguranca_http import CabecalhosDeSeguranca

log = logging.getLogger("gateway")
WEB = Path(__file__).parent / "web"

# Cabeçalhos que passam da tela para o serviço e do serviço para a tela
CABECALHOS_IDA = ("authorization", "content-type", "accept")
CABECALHOS_VOLTA = ("content-type", "www-authenticate")
METODOS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

# Os testes trocam por um httpx.MockTransport para simular os serviços
transporte: httpx.AsyncBaseTransport | None = None


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    app.state.cliente = httpx.AsyncClient(timeout=TIMEOUT_SEGUNDOS, transport=transporte)
    yield
    await app.state.cliente.aclose()


app = FastAPI(
    title="HelpDesk TI · API Gateway", version="3.0.0", lifespan=ciclo_de_vida,
    docs_url=None, redoc_url=None, openapi_url=None,
)
app.add_middleware(CabecalhosDeSeguranca)


# ---------- saúde ----------

async def _no_ar(cliente: httpx.AsyncClient, url: str) -> bool:
    try:
        resposta = await cliente.get(f"{url}/saude", timeout=2)
        return resposta.status_code == 200
    except httpx.HTTPError:
        return False


@app.get("/saude")
async def saude(request: Request):
    """Mostra quais serviços estão no ar."""
    cliente = request.app.state.cliente
    resultados = await asyncio.gather(*(_no_ar(cliente, url) for url in SERVICOS.values()))
    servicos = {nome: ("no ar" if ok else "fora do ar") for nome, ok in zip(SERVICOS, resultados)}
    return {"status": "ok" if all(resultados) else "degradado", "gateway": "no ar", "servicos": servicos}


# ---------- tela ----------

@app.get("/", include_in_schema=False)
def tela_inicial():
    return FileResponse(WEB / "index.html")


@app.get("/app.js", include_in_schema=False)
def script():
    return FileResponse(WEB / "app.js", media_type="text/javascript")


@app.get("/estilo.css", include_in_schema=False)
def estilo():
    return FileResponse(WEB / "estilo.css", media_type="text/css")


# ---------- encaminhamento ----------

@app.api_route("/{caminho:path}", methods=METODOS, include_in_schema=False)
async def encaminhar(caminho: str, request: Request):
    prefixo = caminho.split("/", 1)[0]
    if prefixo not in ROTAS:
        return JSONResponse(status_code=404, content={"detail": "Rota não encontrada."})
    nome, url_base = ROTAS[prefixo]

    cabecalhos = {k: v for k, v in request.headers.items() if k.lower() in CABECALHOS_IDA}
    # O gateway informa o endereço real de quem chamou (usado no limite de tentativas de login).
    # Substitui qualquer X-Forwarded-For enviado pelo cliente, que poderia ser falso.
    cabecalhos["X-Forwarded-For"] = request.client.host if request.client else "desconhecido"

    try:
        resposta = await request.app.state.cliente.request(
            request.method, f"{url_base}/{caminho}", params=request.query_params,
            content=await request.body(), headers=cabecalhos,
        )
    except httpx.TimeoutException:
        log.warning("Tempo esgotado no serviço %s", nome)
        return JSONResponse(status_code=503, content={"detail": f"O serviço de {nome} demorou demais para responder."})
    except httpx.HTTPError:
        log.warning("Serviço %s fora do ar", nome)
        return JSONResponse(status_code=503, content={"detail": f"O serviço de {nome} está fora do ar. Tente de novo em instantes."})

    volta = {k: v for k, v in resposta.headers.items() if k.lower() in CABECALHOS_VOLTA}
    return Response(content=resposta.content, status_code=resposta.status_code, headers=volta)
