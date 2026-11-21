def abrir(cliente, h, ativo_id=1, prioridade="alta", **extra):
    """Abre um chamado pela API. ativo_id=None abre sem equipamento."""
    dados = {"titulo": "PC nao liga", "descricao": "Nada acontece", "prioridade": prioridade, **extra}
    if ativo_id is not None:
        dados["ativo_id"] = ativo_id
    return cliente.post("/chamados", headers=h, json=dados)