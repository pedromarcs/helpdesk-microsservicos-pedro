import os

# Variáveis de teste: precisam existir ANTES de importar o app
os.environ["JWT_SEGREDO"] = "segredo-de-teste-com-mais-de-32-caracteres-1234"
os.environ["DADOS_EXEMPLO"] = "0"
os.environ["DATABASE_URL"] = "sqlite://"

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import config
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