import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app


class Servicos:
    """Usuários, Inventário e Chamados de mentira: anotam o que o gateway encaminhou."""

    def __init__(self):
        self.pedidos = []    # tudo o que o gateway enviou aos serviços
        self.fora = set()    # serviços fora do ar: "usuarios", "inventario", "chamados"
        self.lentos = set()  # serviços que estouram o tempo limite

    def tratar(self, pedido: httpx.Request) -> httpx.Response:
        self.pedidos.append(pedido)
        servico = pedido.url.host  # o gateway chama http://usuarios:8000, http://inventario:8000...
        if servico in self.fora:
            raise httpx.ConnectError("servico fora do ar", request=pedido)
        if servico in self.lentos:
            raise httpx.ReadTimeout("servico demorou demais", request=pedido)
        if pedido.url.path == "/saude":
            return httpx.Response(200, json={"status": "ok", "servico": servico})
        return httpx.Response(200, json={"servico": servico, "caminho": pedido.url.path})


@pytest.fixture
def servicos():
    return Servicos()


@pytest.fixture
def cliente(servicos):
    with TestClient(app) as c:
        # troca o cliente HTTP de verdade pelo de mentira
        app.state.cliente = httpx.AsyncClient(transport=httpx.MockTransport(servicos.tratar))
        yield c