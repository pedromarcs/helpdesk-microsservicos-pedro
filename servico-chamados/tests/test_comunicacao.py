"""Comunicação entre serviços: repasse do token, tempo limite e falhas (requisitos 3, 4 e 8)."""
from tests.helpers import abrir


def test_repassa_o_token_ao_inventario(cliente, contas, mundo):
    abrir(cliente, contas["ana"]["headers"], ativo_id=1)
    url, autorizacao = mundo.chamadas[-1]
    assert url.endswith("/ativos/1")
    assert autorizacao == contas["ana"]["headers"]["Authorization"]


def test_repassa_o_token_ao_servico_de_usuarios(cliente, contas, mundo):
    cid = abrir(cliente, contas["ana"]["headers"], ativo_id=None).json()["id"]
    tec = contas["carla"]["headers"]
    cliente.patch(f"/chamados/{cid}/atribuir", headers=tec, json={"tecnico_id": 4})
    url, autorizacao = mundo.chamadas[-1]
    assert url.endswith("/usuarios/4") and autorizacao == tec["Authorization"]


def test_inventario_fora_do_ar_devolve_503_e_nao_grava(cliente, contas, mundo):
    mundo.fora.add("inventario")
    r = abrir(cliente, contas["ana"]["headers"], ativo_id=1)
    assert r.status_code == 503 and "inventário" in r.json()["detail"]
    assert cliente.get("/chamados", headers=contas["carla"]["headers"]).json() == []


def test_inventario_fora_nao_impede_chamado_sem_equipamento(cliente, contas, mundo):
    mundo.fora.add("inventario")
    assert abrir(cliente, contas["ana"]["headers"], ativo_id=None).status_code == 201


def test_servico_lento_estoura_o_tempo_limite_e_vira_503(cliente, contas, mundo):
    mundo.lentos.add("inventario")
    r = abrir(cliente, contas["ana"]["headers"], ativo_id=1)
    assert r.status_code == 503


def test_erro_inesperado_do_outro_servico_vira_503(cliente, contas, mundo):
    mundo.erros["inventario"] = 500
    assert abrir(cliente, contas["ana"]["headers"], ativo_id=1).status_code == 503


def test_usuarios_fora_do_ar_nao_atribui_e_mantem_o_chamado(cliente, contas, mundo):
    cid = abrir(cliente, contas["ana"]["headers"], ativo_id=None).json()["id"]
    tec = contas["carla"]["headers"]
    mundo.fora.add("usuarios")
    r = cliente.patch(f"/chamados/{cid}/atribuir", headers=tec, json={"tecnico_id": 4})
    assert r.status_code == 503 and "usuários" in r.json()["detail"]
    chamado = cliente.get(f"/chamados/{cid}", headers=tec).json()
    assert chamado["status"] == "aberto" and chamado["tecnico_id"] is None


def test_listar_continua_funcionando_com_os_outros_servicos_fora(cliente, contas, mundo):
    abrir(cliente, contas["ana"]["headers"], ativo_id=None)
    mundo.fora.update({"usuarios", "inventario"})
    tec = contas["carla"]["headers"]
    assert len(cliente.get("/chamados", headers=tec).json()) == 1
    assert cliente.get("/chamados/painel", headers=tec).status_code == 200