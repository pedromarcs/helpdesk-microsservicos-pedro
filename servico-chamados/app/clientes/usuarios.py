"""Cliente do serviço de Usuários."""
from app.clientes.comum import buscar
from app.config import USUARIOS_URL
from app.erros import RegraDeNegocio


def obter_tecnico(tecnico_id: int, token: str) -> dict:
    """Confere que o usuário existe e é técnico. Era `usuarios.obter_tecnico(db, id)`."""
    usuario = buscar("usuários", f"{USUARIOS_URL}/usuarios/{tecnico_id}", token)
    if usuario.get("perfil") != "tecnico":
        raise RegraDeNegocio(f"Usuário {tecnico_id} não é técnico.")
    return usuario