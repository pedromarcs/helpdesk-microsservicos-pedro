import os

# Variáveis de teste: precisam existir ANTES de importar o app
os.environ["JWT_SEGREDO"] = "segredo-de-teste-com-mais-de-32-caracteres-1234"
os.environ["DADOS_EXEMPLO"] = "0"
os.environ["DATABASE_URL"] = "sqlite://"

from datetime import datetime, timedelta, timezone

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import config
from app.clientes import comum
from app.database import Base, get_db
from app.main import app


def fazer_token(usuario_id, perfil, *, segredo=None, sem=(), **mudar):
    """Fabrica um token como o serviço de Usuários faria. `sem` tira campos; `mudar` troca campos."""
    agora = datetime.now(timezone.utc)
    dados = {"sub": str(usuario_id), "perfil": perfil, "iat": agora, "exp": agora + timedelta(hours=1),
             "iss": config.JWT_EMISSOR}
    dados.update(mudar)
    for campo in sem:
        dados.pop(campo, None)
    return jwt.encode(dados, segredo or config.JWT_SEGREDO, algorithm="HS256")


class Mundo:
    """Usuários e Inventário de mentira: respondem como os de verdade e podem ser derrubados."""

    def __init__(self):
        self.usuarios = {
            1: {"id": 1, "nome": "Admin", "perfil": "admin"},
            2: {"id": 2, "nome": "Ana", "perfil": "solicitante"},
            3: {"id": 3, "nome": "Bia", "perfil": "solicitante"},
            4: {"id": 4, "nome": "Carla", "perfil": "tecnico"},
        }
        self.ativos = {1: {"id": 1, "patrimonio": "PAT-1", "tipo": "computador", "descricao": "Desktop", "setor": "TI"}}
        self.fora = set()      # serviços fora do ar: "usuarios", "inventario"
        self.lentos = set()    # serviços que estouram o tempo limite
        self.erros = {}        # serviço -> código de erro inesperado (ex.: 500)
        self.chamadas = []     # (url, cabeçalho Authorization) de cada chamada feita

    def get(self, url, headers=None, timeout=None):
        self.chamadas.append((url, (headers or {}).get("Authorization")))
        servico = "usuarios" if "/usuarios/" in url else "inventario"
        if servico in self.fora:
            raise httpx.ConnectError("servico fora do ar")
        if servico in self.lentos:
            raise httpx.ReadTimeout("servico demorou demais")
        pedido = httpx.Request("GET", url)
        if servico in self.erros:
            return httpx.Response(self.erros[servico], json={"detail": "erro interno"}, request=pedido)
        tabela = self.usuarios if servico == "usuarios" else self.ativos
        item_id = int(url.rsplit("/", 1)[1])
        if item_id not in tabela:
            nome = "Usuário" if servico == "usuarios" else "Ativo"
            return httpx.Response(404, json={"detail": f"{nome} {item_id} não encontrado."}, request=pedido)
        return httpx.Response(200, json=tabela[item_id], request=pedido)


@pytest.fixture
def mundo(monkeypatch):
    m = Mundo()
    monkeypatch.setattr(comum.httpx, "get", m.get)
    return m


@pytest.fixture
def token():
    return fazer_token


@pytest.fixture
def contas():
    """Mesmos ids dos dados de exemplo: admin=1, ana=2, bia=3, carla=4."""
    quem = {"admin": (1, "admin"), "ana": (2, "solicitante"), "bia": (3, "solicitante"), "carla": (4, "tecnico")}
    return {apelido: {"headers": {"Authorization": f"Bearer {fazer_token(i, perfil)}"}, "id": i}
            for apelido, (i, perfil) in quem.items()}


@pytest.fixture
def sessao():
    """Banco novo, em memória, para cada teste."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def db_de_teste():
        db = Sessao()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = db_de_teste
    yield Sessao
    app.dependency_overrides.clear()


@pytest.fixture
def cliente(sessao):
    with TestClient(app) as c:
        yield c