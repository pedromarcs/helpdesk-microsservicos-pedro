"""Testes de segurança do serviço de Inventário: tokens, perfis e validação de entrada."""
from datetime import datetime, timedelta, timezone

import jwt

from app import config

ATIVO = {"patrimonio": "PAT-9", "tipo": "outro", "descricao": "X", "setor": "TI"}


def com(token_jwt):
    return {"Authorization": f"Bearer {token_jwt}"}


# ---------- autenticação ----------

def test_rotas_exigem_login(cliente, contas):
    for metodo, rota in [("get", "/ativos"), ("get", "/ativos/1"), ("post", "/ativos")]:
        assert getattr(cliente, metodo)(rota).status_code == 401, rota


def test_token_adulterado(cliente, contas):
    h = {"Authorization": contas["ana"]["headers"]["Authorization"] + "x"}
    assert cliente.get("/ativos", headers=h).status_code == 401


def test_token_assinado_com_outro_segredo(cliente, token):
    falso = token(1, "admin", segredo="segredo-de-outra-pessoa-com-mais-de-32-caracteres")
    assert cliente.get("/ativos", headers=com(falso)).status_code == 401


def test_token_sem_assinatura_alg_none(cliente):
    agora = datetime.now(timezone.utc)
    falso = jwt.encode({"sub": "1", "perfil": "admin", "iss": config.JWT_EMISSOR,
                        "iat": agora, "exp": agora + timedelta(hours=1)}, None, algorithm="none")
    assert cliente.get("/ativos", headers=com(falso)).status_code == 401


def test_token_expirado(cliente, token):
    antigo = datetime.now(timezone.utc) - timedelta(hours=2)
    vencido = token(2, "solicitante", iat=antigo, exp=antigo + timedelta(minutes=5))
    assert cliente.get("/ativos", headers=com(vencido)).status_code == 401


def test_token_sem_perfil_e_recusado(cliente, token):
    assert cliente.get("/ativos", headers=com(token(2, "solicitante", sem=("perfil",)))).status_code == 401


def test_perfil_inventado_nao_ganha_privilegio(cliente, token):
    assert cliente.get("/ativos", headers=com(token(2, "superadmin"))).status_code == 401


def test_token_de_outro_emissor(cliente, token):
    assert cliente.get("/ativos", headers=com(token(2, "solicitante", iss="outro-sistema"))).status_code == 401


# ---------- permissões, entrada e respostas ----------

def test_solicitante_nao_cadastra_ativo(cliente, contas):
    assert cliente.post("/ativos", headers=contas["ana"]["headers"], json=ATIVO).status_code == 403


def test_solicitante_pode_listar_ativos(cliente, contas):
    assert cliente.get("/ativos", headers=contas["ana"]["headers"]).status_code == 200


def test_requisicao_grande_demais(cliente, contas):
    corpo = '{"patrimonio": "' + "x" * 70000 + '"}'
    r = cliente.post("/ativos", headers={**contas["carla"]["headers"], "Content-Type": "application/json"}, content=corpo)
    assert r.status_code == 413


def test_cabecalhos_de_seguranca(cliente):
    r = cliente.get("/saude")
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"