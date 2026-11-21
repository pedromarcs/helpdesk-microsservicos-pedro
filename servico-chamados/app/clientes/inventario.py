"""Cliente do serviço de Inventário."""
from app.clientes.comum import buscar
from app.config import INVENTARIO_URL


def obter_ativo(ativo_id: int, token: str) -> dict:
    """Confere que o equipamento existe. Era `inventario.obter(db, id)`."""
    return buscar("inventário", f"{INVENTARIO_URL}/ativos/{ativo_id}", token)