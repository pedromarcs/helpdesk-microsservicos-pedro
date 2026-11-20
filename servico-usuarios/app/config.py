"""Configurações do serviço de Usuários, lidas das variáveis de ambiente."""
import logging
import os

log = logging.getLogger("usuarios")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./usuarios.db")

# Segredo que assina os tokens JWT. TODOS os serviços precisam do MESMO valor,
# por isso ele é obrigatório: se faltar, o serviço não sobe.
JWT_SEGREDO = os.getenv("JWT_SEGREDO") or ""
if len(JWT_SEGREDO) < 32:
    raise RuntimeError(
        "Defina JWT_SEGREDO (mínimo de 32 caracteres) no arquivo .env. "
        "Todos os serviços precisam usar o mesmo segredo."
    )

JWT_ALGORITMO = "HS256"
JWT_EMISSOR = "helpdesk-ti"
TOKEN_MINUTOS = int(os.getenv("TOKEN_MINUTOS", "60"))

# Proteção contra tentativas de adivinhar senhas
LOGIN_MAX_FALHAS = int(os.getenv("LOGIN_MAX_FALHAS", "5"))
LOGIN_JANELA_SEGUNDOS = int(os.getenv("LOGIN_JANELA_SEGUNDOS", "300"))

# Tamanho máximo do corpo de uma requisição (em bytes)
TAMANHO_MAXIMO_REQUISICAO = 64 * 1024

DOCS_ATIVA = os.getenv("DOCS", "1") == "1"