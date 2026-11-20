"""Cria os usuários de exemplo quando o banco está vazio (só para aula).

A ordem importa: os ids ficam admin=1, ana=2, bruno=3, carla=4, diego=5.
Os outros serviços vão usar esses números (por exemplo, o técnico Carla é o 4).
"""
import os

from sqlalchemy.orm import Session

from app.usuarios import servico as usuarios
from app.usuarios.esquemas import UsuarioCriar

SENHA = os.getenv("SENHA_EXEMPLO", "Helpdesk2026")


def carregar(db: Session) -> None:
    if usuarios.listar(db):
        return
    novo = lambda nome, email, perfil: usuarios.criar(db, UsuarioCriar(nome=nome, email=email, perfil=perfil, senha=SENHA))
    novo("Admin TI", "admin@empresa.com", "admin")
    novo("Ana Souza", "ana@empresa.com", "solicitante")
    novo("Bruno Lima", "bruno@empresa.com", "solicitante")
    novo("Carla Dias", "carla@empresa.com", "tecnico")
    novo("Diego Rocha", "diego@empresa.com", "tecnico")