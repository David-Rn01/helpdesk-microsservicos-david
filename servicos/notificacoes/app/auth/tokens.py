"""Validação dos tokens JWT criados pelo serviço de Usuários (este serviço só lê)."""
import jwt

from app.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO


class TokenInvalido(Exception):
    pass


def ler(token: str) -> dict:
    """Devolve {'id': ..., 'perfil': ...} do token, ou lança TokenInvalido."""
    try:
        dados = jwt.decode(
            token, JWT_SEGREDO, algorithms=[JWT_ALGORITMO], issuer=JWT_EMISSOR,
            options={"require": ["exp", "iat", "sub", "iss"]},
        )
        return {"id": int(dados["sub"]), "perfil": str(dados["perfil"])}
    except (jwt.PyJWTError, ValueError, KeyError) as erro:
        raise TokenInvalido() from erro
