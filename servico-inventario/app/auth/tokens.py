"""Conferência dos tokens JWT.

Este serviço só CONFERE tokens. Quem cria é o serviço de Usuários.
"""
from dataclasses import dataclass

import jwt

from app.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO

PERFIS_VALIDOS = {"solicitante", "tecnico", "admin"}


class TokenInvalido(Exception):
    pass


@dataclass(frozen=True)
class UsuarioDoToken:
    """O que sabemos sobre quem fez a requisição: só o que está no token."""
    id: int
    perfil: str


def ler(token: str) -> UsuarioDoToken:
    """Devolve quem é o dono do token, ou lança TokenInvalido."""
    try:
        dados = jwt.decode(
            token, JWT_SEGREDO, algorithms=[JWT_ALGORITMO], issuer=JWT_EMISSOR,
            options={"require": ["exp", "iat", "sub", "iss"]},
        )
        perfil = dados["perfil"]
        if perfil not in PERFIS_VALIDOS:
            raise ValueError("perfil desconhecido")
        return UsuarioDoToken(id=int(dados["sub"]), perfil=perfil)
    except (jwt.PyJWTError, ValueError, KeyError) as erro:
        raise TokenInvalido() from erro