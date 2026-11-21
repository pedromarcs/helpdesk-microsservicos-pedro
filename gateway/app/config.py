"""Configurações do API Gateway, lidas das variáveis de ambiente."""
import os

# Endereços dos serviços. Dentro do Docker Compose eles se chamam pelo NOME do serviço.
USUARIOS_URL = os.getenv("USUARIOS_URL", "http://usuarios:8000").rstrip("/")
INVENTARIO_URL = os.getenv("INVENTARIO_URL", "http://inventario:8000").rstrip("/")
CHAMADOS_URL = os.getenv("CHAMADOS_URL", "http://chamados:8000").rstrip("/")

# Quanto o gateway espera por um serviço (em segundos). Fica MAIOR que o tempo limite
# do serviço de Chamados (3 s por chamada), para o 503 dele chegar antes do 504 daqui.
TIMEOUT_GATEWAY = float(os.getenv("TIMEOUT_GATEWAY", "10"))
TIMEOUT_SAUDE = 2.0

# Tamanho máximo do corpo de uma requisição (em bytes)
TAMANHO_MAXIMO_REQUISICAO = 64 * 1024