"""Chamadas HTTP ao serviço de Usuários."""
from app.clientes import buscar
from app.config import USUARIOS_URL
from app.erros import RegraDeNegocio


def obter_tecnico(usuario_id: int, token: str) -> dict:
    """GET /usuarios/{id} e confere se o usuário é técnico."""
    usuario = buscar(USUARIOS_URL, f"/usuarios/{usuario_id}", token, "usuários",
                     f"Usuário {usuario_id} não encontrado.")
    if usuario.get("perfil") != "tecnico":
        raise RegraDeNegocio(f"Usuário {usuario_id} não é técnico.")
    return usuario
