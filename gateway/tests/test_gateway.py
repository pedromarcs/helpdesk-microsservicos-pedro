"""Testes do API Gateway: roteamento, repasse do token, falhas e segurança da tela."""
import json
from pathlib import Path


# ---------- roteamento ----------

def test_encaminha_cada_rota_para_o_servico_certo(cliente, servicos):
    rotas = {"/auth/login": "usuarios", "/usuarios": "usuarios", "/usuarios/4": "usuarios",
             "/ativos": "inventario", "/ativos/1": "inventario",
             "/chamados": "chamados", "/chamados/painel": "chamados", "/notificacoes": "chamados"}
    for rota, servico in rotas.items():
        r = cliente.get(rota)
        assert r.status_code == 200 and r.json() == {"servico": servico, "caminho": rota}, rota


def test_repassa_metodo_corpo_e_parametros(cliente, servicos):
    cliente.post("/chamados?status=aberto", json={"titulo": "oi"})
    pedido = servicos.pedidos[-1]
    assert pedido.method == "POST" and pedido.url.query == b"status=aberto"
    assert json.loads(pedido.content) == {"titulo": "oi"}


def test_rota_desconhecida_devolve_404(cliente, servicos):
    assert cliente.get("/qualquer-coisa").status_code == 404
    assert servicos.pedidos == []  # nem chegou a chamar um serviço


def test_documentacao_dos_servicos_nao_e_exposta(cliente):
    for rota in ("/docs", "/openapi.json", "/redoc"):
        assert cliente.get(rota).status_code == 404, rota


# ---------- token: o gateway só repassa, quem confere é cada serviço ----------

def test_repassa_o_cabecalho_authorization(cliente, servicos):
    cliente.get("/chamados", headers={"Authorization": "Bearer qualquer-coisa"})
    assert servicos.pedidos[-1].headers["authorization"] == "Bearer qualquer-coisa"


def test_nao_inventa_credencial(cliente, servicos):
    cliente.get("/chamados")
    assert "authorization" not in servicos.pedidos[-1].headers


# ---------- falhas ----------

def test_servico_fora_do_ar_devolve_503(cliente, servicos):
    servicos.fora.add("inventario")
    r = cliente.get("/ativos")
    assert r.status_code == 503 and "inventário" in r.json()["detail"]
    assert cliente.get("/chamados").status_code == 200  # os outros continuam


def test_servico_lento_devolve_504(cliente, servicos):
    servicos.lentos.add("chamados")
    r = cliente.get("/chamados")
    assert r.status_code == 504 and "demorou demais" in r.json()["detail"]


def test_saude_mostra_quem_esta_no_ar(cliente, servicos):
    assert cliente.get("/saude").json() == {
        "gateway": "ok", "status": "ok", "servicos": {"usuarios": "ok", "inventario": "ok", "chamados": "ok"}}
    servicos.fora.add("inventario")
    r = cliente.get("/saude").json()
    assert r["status"] == "degradado"
    assert r["servicos"]["inventario"] == "fora do ar" and r["servicos"]["usuarios"] == "ok"


# ---------- tela e cabeçalhos ----------

def test_tela_e_servida_pelo_gateway(cliente, servicos):
    assert "HelpDesk TI" in cliente.get("/").text
    assert cliente.get("/app.js").headers["content-type"].startswith("text/javascript")
    assert cliente.get("/estilo.css").headers["content-type"].startswith("text/css")
    assert servicos.pedidos == []


def test_tela_escapa_o_html():
    js = (Path(__file__).parent.parent / "app" / "web" / "app.js").read_text(encoding="utf-8")
    assert "const esc =" in js and "onclick" not in js


def test_cabecalhos_de_seguranca(cliente):
    r = cliente.get("/")
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"


def test_requisicao_grande_demais(cliente, servicos):
    corpo = '{"titulo": "' + "x" * 70000 + '"}'
    r = cliente.post("/chamados", headers={"Content-Type": "application/json"}, content=corpo)
    assert r.status_code == 413 and servicos.pedidos == []