"""Configurações do serviço de Chamados, lidas das variáveis de ambiente."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chamados.db")

# Segredo para CONFERIR os tokens. Precisa ser o mesmo do serviço de Usuários.
JWT_SEGREDO = os.getenv("JWT_SEGREDO") or ""
if len(JWT_SEGREDO) < 32:
    raise RuntimeError(
        "Defina JWT_SEGREDO (mínimo de 32 caracteres) no arquivo .env. "
        "Todos os serviços precisam usar o mesmo segredo."
    )

JWT_ALGORITMO = "HS256"
JWT_EMISSOR = "helpdesk-ti"

# Endereços dos outros serviços. Dentro do Docker Compose eles se chamam pelo NOME
# do serviço (usuarios, inventario), nunca por localhost.
USUARIOS_URL = os.getenv("USUARIOS_URL", "http://usuarios:8000").rstrip("/")
INVENTARIO_URL = os.getenv("INVENTARIO_URL", "http://inventario:8000").rstrip("/")

# Quanto esperar (em segundos) por uma resposta de outro serviço antes de desistir
TIMEOUT_SERVICOS = float(os.getenv("TIMEOUT_SERVICOS", "3"))

# Tamanho máximo do corpo de uma requisição (em bytes)
TAMANHO_MAXIMO_REQUISICAO = 64 * 1024

DOCS_ATIVA = os.getenv("DOCS", "1") == "1"