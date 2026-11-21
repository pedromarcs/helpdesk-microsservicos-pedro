def novo(patrimonio="PAT-1", tipo="computador", descricao="Desktop", setor="TI", **extra):
    return {"patrimonio": patrimonio, "tipo": tipo, "descricao": descricao, "setor": setor, **extra}


def test_tecnico_cadastra_ativo_e_filtra_por_setor(cliente, contas):
    h = contas["carla"]["headers"]
    cliente.post("/ativos", headers=h, json=novo("PAT-1", "impressora", "HP", "RH"))
    cliente.post("/ativos", headers=h, json=novo("PAT-2", "computador", "Dell", "TI"))
    assert len(cliente.get("/ativos", params={"setor": "RH"}, headers=h).json()) == 1


def test_admin_tambem_cadastra(cliente, contas):
    assert cliente.post("/ativos", headers=contas["admin"]["headers"], json=novo()).status_code == 201


def test_obter_ativo(cliente, contas):
    criado = cliente.post("/ativos", headers=contas["carla"]["headers"], json=novo()).json()
    r = cliente.get(f"/ativos/{criado['id']}", headers=contas["ana"]["headers"])
    assert r.status_code == 200 and r.json()["patrimonio"] == "PAT-1"


def test_ativo_inexistente(cliente, contas):
    r = cliente.get("/ativos/99", headers=contas["ana"]["headers"])
    assert r.status_code == 404 and r.json()["detail"] == "Ativo 99 não encontrado."


def test_patrimonio_repetido_e_recusado(cliente, contas):
    h = contas["carla"]["headers"]
    cliente.post("/ativos", headers=h, json=novo())
    assert cliente.post("/ativos", headers=h, json=novo()).status_code == 422


def test_campos_extras_sao_recusados(cliente, contas):
    assert cliente.post("/ativos", headers=contas["carla"]["headers"], json=novo(id=50)).status_code == 422


def test_patrimonio_com_caracteres_invalidos(cliente, contas):
    assert cliente.post("/ativos", headers=contas["carla"]["headers"], json=novo("PAT 1; DROP")).status_code == 422


def test_saude(cliente):
    assert cliente.get("/saude").json() == {"status": "ok", "servico": "inventario"}