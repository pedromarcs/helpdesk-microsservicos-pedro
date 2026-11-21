"""Configurações do serviço de Inventário, lidas das variáveis de ambiente."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventario.db")

# Segredo para CONFERIR os tokens. Precisa ser o mesmo do serviço de Usuários
# (que é quem cria os tokens). Se faltar, o serviço não sobe.
JWT_SEGREDO = os.getenv("JWT_SEGREDO") or ""
if len(JWT_SEGREDO) < 32:
    raise RuntimeError(
        "Defina JWT_SEGREDO (mínimo de 32 caracteres) no arquivo .env. "
        "Todos os serviços precisam usar o mesmo segredo."
    )

JWT_ALGORITMO = "HS256"
JWT_EMISSOR = "helpdesk-ti"

# Tamanho máximo do corpo de uma requisição (em bytes)
TAMANHO_MAXIMO_REQUISICAO = 64 * 1024

DOCS_ATIVA = os.getenv("DOCS", "1") == "1"