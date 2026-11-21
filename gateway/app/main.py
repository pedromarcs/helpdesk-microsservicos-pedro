"""API Gateway (HelpDesk TI).

Único ponto de entrada do sistema (porta 8000). Serve a tela e encaminha cada rota
para o serviço certo. NÃO confere o token: só repassa o cabeçalho Authorization, e
cada serviço faz a sua própria conferência.
"""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse

from app.config import CHAMADOS_URL, INVENTARIO_URL, TIMEOUT_GATEWAY, TIMEOUT_SAUDE, USUARIOS_URL
from app.seguranca_http import CabecalhosDeSeguranca

WEB = Path(__file__).parent / "web"

# Primeiro pedaço da rota -> (nome do serviço, endereço dele)
ROTAS = {
    "auth": ("usuários", USUARIOS_URL),
    "usuarios": ("usuários", USUARIOS_URL),
    "ativos": ("inventário", INVENTARIO_URL),
    "chamados": ("chamados", CHAMADOS_URL),
    "notificacoes": ("chamados", CHAMADOS_URL),
}

SERVICOS = {"usuarios": USUARIOS_URL, "inventario": INVENTARIO_URL, "chamados": CHAMADOS_URL}

# Cabeçalhos que não devem ser repassados (são de uma conexão só, não da mensagem)
NA_IDA = {"host", "content-length", "connection", "keep-alive", "transfer-encoding", "upgrade",
          "te", "trailer", "accept-encoding", "proxy-authorization", "proxy-authenticate"}
NA_VOLTA = {"content-length", "content-encoding", "connection", "keep-alive", "transfer-encoding",
            "upgrade", "te", "trailer"}


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    app.state.cliente = httpx.AsyncClient(timeout=TIMEOUT_GATEWAY)
    yield
    await app.state.cliente.aclose()


app = FastAPI(
    title="HelpDesk TI · API Gateway", version="3.0.0", lifespan=ciclo_de_vida,
    docs_url=None, redoc_url=None, openapi_url=None,
)
app.add_middleware(CabecalhosDeSeguranca)


@app.get("/", include_in_schema=False)
def tela_inicial():
    return FileResponse(WEB / "index.html")


@app.get("/app.js", include_in_schema=False)
def script():
    return FileResponse(WEB / "app.js", media_type="text/javascript")


@app.get("/estilo.css", include_in_schema=False)
def estilo():
    return FileResponse(WEB / "estilo.css", media_type="text/css")


@app.get("/saude")
async def saude(request: Request):
    """Mostra quais serviços estão no ar."""
    async def conferir(nome: str, base: str):
        try:
            r = await request.app.state.cliente.get(f"{base}/saude", timeout=TIMEOUT_SAUDE)
            return nome, "ok" if r.status_code == 200 else "com problemas"
        except httpx.HTTPError:
            return nome, "fora do ar"

    servicos = dict(await asyncio.gather(*(conferir(n, b) for n, b in SERVICOS.items())))
    tudo_ok = all(estado == "ok" for estado in servicos.values())
    return {"gateway": "ok", "status": "ok" if tudo_ok else "degradado", "servicos": servicos}


@app.api_route("/{caminho:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
async def encaminhar(caminho: str, request: Request):
    """Repassa a requisição ao serviço dono da rota e devolve a resposta dele."""
    partes = caminho.split("/")
    if partes[0] not in ROTAS or ".." in partes:
        return JSONResponse(status_code=404, content={"detail": "Rota não encontrada."})

    nome, base = ROTAS[partes[0]]
    url = f"{base}/{quote(caminho, safe='/')}"
    if request.url.query:
        url += f"?{request.url.query}"
    cabecalhos = {k: v for k, v in request.headers.items() if k.lower() not in NA_IDA}

    try:
        resposta = await request.app.state.cliente.request(
            request.method, url, headers=cabecalhos, content=await request.body()
        )
    except httpx.TimeoutException:
        return JSONResponse(status_code=504, content={"detail": f"O serviço de {nome} demorou demais para responder."})
    except httpx.HTTPError:
        return JSONResponse(
            status_code=503,
            content={"detail": f"O serviço de {nome} está indisponível no momento. Tente novamente em instantes."},
        )

    devolver = {k: v for k, v in resposta.headers.items() if k.lower() not in NA_VOLTA}
    return Response(content=resposta.content, status_code=resposta.status_code, headers=devolver)