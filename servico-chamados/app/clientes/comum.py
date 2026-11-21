"""Chamadas HTTP a outros serviços, com tempo limite e tratamento de falhas."""
import logging

import httpx

from app.config import TIMEOUT_SERVICOS
from app.erros import NaoEncontrado, ServicoIndisponivel

log = logging.getLogger("chamados")


def _detalhe(resposta: httpx.Response, padrao: str) -> str:
    try:
        corpo = resposta.json()
        return str(corpo.get("detail", padrao)) if isinstance(corpo, dict) else padrao
    except ValueError:
        return padrao


def buscar(servico: str, url: str, token: str) -> dict:
    """GET em outro serviço, repassando o token de quem fez a requisição.

    - 200: devolve o JSON;
    - 404: vira NaoEncontrado (a tela continua vendo o mesmo erro do monólito);
    - fora do ar, sem resposta no tempo limite ou erro inesperado: vira ServicoIndisponivel (503).
    """
    try:
        resposta = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT_SERVICOS)
    except httpx.HTTPError as erro:  # tempo esgotado, conexão recusada, nome não encontrado...
        log.warning("Falha ao chamar o serviço de %s (%s): %s", servico, url, type(erro).__name__)
        raise ServicoIndisponivel(
            f"O serviço de {servico} está indisponível no momento. Tente novamente em instantes."
        ) from erro

    if resposta.status_code == 200:
        return resposta.json()
    if resposta.status_code == 404:
        raise NaoEncontrado(_detalhe(resposta, "Recurso não encontrado."))

    log.warning("O serviço de %s respondeu %s em %s", servico, resposta.status_code, url)
    raise ServicoIndisponivel(f"O serviço de {servico} respondeu com erro ({resposta.status_code}).")