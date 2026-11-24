"""Publica eventos na fila (Redis) para o serviço de Notificações.

Se a fila estiver fora do ar, o erro é só registrado no log: o chamado
continua sendo aberto, atribuído ou resolvido normalmente.
"""
import json
import logging
from datetime import datetime

from app.config import FILA_EVENTOS, REDIS_URL

log = logging.getLogger("chamados.eventos")
_conexao = None


def _redis():
    global _conexao
    if _conexao is None:
        import redis
        _conexao = redis.Redis.from_url(REDIS_URL, socket_timeout=1, socket_connect_timeout=1)
    return _conexao


def publicar(tipo: str, destinatario_id: int, mensagem: str) -> bool:
    """Publica o evento. Devolve False (sem lançar erro) se a fila não estiver disponível."""
    if not REDIS_URL:
        return False
    evento = {"tipo": tipo, "destinatario_id": destinatario_id, "mensagem": mensagem,
              "criado_em": datetime.now().isoformat()}
    try:
        _redis().lpush(FILA_EVENTOS, json.dumps(evento))
        return True
    except Exception as erro:  # a fila nunca pode derrubar o chamado
        log.warning("Evento %s não publicado: %s", tipo, erro)
        return False
