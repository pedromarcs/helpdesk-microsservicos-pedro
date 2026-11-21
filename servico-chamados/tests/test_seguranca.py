"""Testes de segurança do serviço de Chamados: tokens, permissões e validação de entrada."""
from datetime import datetime, timedelta, timezone

import jwt

from app import config
from tests.helpers import abrir


def com(token_jwt):
    return {"Authorization": f"Bearer {token_jwt}"}


# ---------- autenticação ----------

def test_rotas_exigem_login(cliente, contas):
    for metodo, rota in [("get", "/chamados"), ("get", "/chamados/painel"), ("get", "/chamados/1"),
                         ("get", "/notificacoes"), ("post", "/chamados")]:
        assert getattr(cliente, metodo)(rota).status_code == 401, rota


def test_token_adulterado(cliente, contas):
    h = {"Authorization": contas["ana"]["headers"]["Authorization"] + "x"}
    assert cliente.get("/chamados", headers=h).status_code == 401


def test_token_assinado_com_outro_segredo(cliente, token):
    falso = token(1, "admin", segredo="segredo-de-outra-pessoa-com-mais-de-32-caracteres")
    assert cliente.get("/chamados", headers=com(falso)).status_code == 401


def test_token_sem_assinatura_alg_none(cliente):
    agora = datetime.now(timezone.utc)
    falso = jwt.encode({"sub": "1", "perfil": "admin", "iss": config.JWT_EMISSOR,
                        "iat": agora, "exp": agora + timedelta(hours=1)}, None, algorithm="none")
    assert cliente.get("/chamados", headers=com(falso)).status_code == 401


def test_token_expirado(cliente, token):
    antigo = datetime.now(timezone.utc) - timedelta(hours=2)
    vencido = token(2, "solicitante", iat=antigo, exp=antigo + timedelta(minutes=5))
    assert cliente.get("/chamados", headers=com(vencido)).status_code == 401


def test_token_sem_perfil_e_recusado(cliente, token):
    assert cliente.get("/chamados", headers=com(token(2, "solicitante", sem=("perfil",)))).status_code == 401


def test_perfil_inventado_nao_ganha_privilegio(cliente, token):
    assert cliente.get("/chamados", headers=com(token(2, "superadmin"))).status_code == 401


def test_token_de_outro_emissor(cliente, token):
    assert cliente.get("/chamados", headers=com(token(2, "solicitante", iss="outro-sistema"))).status_code == 401


# ---------- permissões ----------

def test_solicitante_nao_ve_chamado_de_outra_pessoa(cliente, contas, mundo):
    cid = abrir(cliente, contas["ana"]["headers"]).json()["id"]
    assert cliente.get(f"/chamados/{cid}", headers=contas["bia"]["headers"]).status_code == 404
    assert cliente.get("/chamados", headers=contas["bia"]["headers"]).json() == []


def test_solicitante_nao_atribui_nem_resolve(cliente, contas, mundo):
    cid = abrir(cliente, contas["ana"]["headers"]).json()["id"]
    h = contas["ana"]["headers"]
    assert cliente.patch(f"/chamados/{cid}/atribuir", headers=h, json={"tecnico_id": 4}).status_code == 403
    assert cliente.patch(f"/chamados/{cid}/status", headers=h, json={"status": "em_atendimento"}).status_code == 403


def test_nao_da_para_abrir_chamado_em_nome_de_outro(cliente, contas, mundo):
    r = abrir(cliente, contas["ana"]["headers"], solicitante_id=contas["bia"]["id"])
    assert r.status_code == 422  # campo extra é recusado


def test_nao_da_para_comentar_em_nome_de_outro(cliente, contas, mundo):
    cid = abrir(cliente, contas["ana"]["headers"]).json()["id"]
    r = cliente.post(f"/chamados/{cid}/comentarios", headers=contas["ana"]["headers"],
                     json={"texto": "oi", "autor_id": contas["carla"]["id"]})
    assert r.status_code == 422


def test_notificacoes_sao_so_do_proprio_usuario(cliente, contas, mundo):
    abrir(cliente, contas["ana"]["headers"])
    assert cliente.get("/notificacoes", headers=contas["bia"]["headers"]).json() == []


# ---------- entrada e respostas ----------

def test_titulo_grande_demais(cliente, contas, mundo):
    assert abrir(cliente, contas["ana"]["headers"], titulo="x" * 500).status_code == 422


def test_requisicao_grande_demais(cliente, contas):
    corpo = '{"titulo": "' + "x" * 70000 + '"}'
    r = cliente.post("/chamados", headers={**contas["ana"]["headers"], "Content-Type": "application/json"}, content=corpo)
    assert r.status_code == 413


def test_texto_com_html_e_guardado_como_texto(cliente, contas, mundo):
    r = abrir(cliente, contas["ana"]["headers"], titulo="<script>alert(1)</script>")
    assert r.status_code == 201 and r.json()["titulo"] == "<script>alert(1)</script>"


def test_cabecalhos_de_seguranca(cliente):
    r = cliente.get("/saude")
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"