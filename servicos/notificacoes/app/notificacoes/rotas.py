from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencias import UsuarioToken, usuario_atual
from app.database import get_db
from app.notificacoes import repositorio
from app.notificacoes.esquemas import NotificacaoSaida

router = APIRouter(prefix="/notificacoes", tags=["Notificações"])


@router.get("", response_model=list[NotificacaoSaida])
def minhas_notificacoes(usuario: UsuarioToken = Depends(usuario_atual), db: Session = Depends(get_db)):
    """Cada usuário vê só as próprias notificações."""
    return repositorio.listar(db, usuario.id)
