"""Consome os eventos publicados pelo serviço de Chamados e grava os avisos.

Roda em uma thread separada. Se o Redis cair, tenta de novo a cada poucos
segundos; os eventos ficam guardados na fila até serem lidos.
"""
import json
import logging
import threading
from datetime import datetime

from app.config import FILA_EVENTOS, REDIS_URL
from app.database import SessionLocal
from app.notificacoes import repositorio

log = logging.getLogger("notificacoes.consumidor")

TIPOS_ACEITOS = {"ChamadoAberto", "ChamadoAtribuido", "ChamadoResolvido"}


def processar(mensagem: str | bytes) -> bool:
    """Grava a notificação de um evento. Devolve False se o evento for inválido."""
    try:
        evento = json.loads(mensagem)
        tipo = str(evento["tipo"])
        destinatario_id = int(evento["destinatario_id"])
        texto = str(evento["mensagem"])[:300]
    except (ValueError, KeyError, TypeError):
        log.warning("Evento inválido ignorado: %r", mensagem)
        return False
    if tipo not in TIPOS_ACEITOS:
        log.warning("Tipo de evento desconhecido ignorado: %s", tipo)
        return False
    with SessionLocal() as db:
        repositorio.notificar(db, tipo, destinatario_id, texto)
    log.info("Notificação gravada: %s para o usuário %s", tipo, destinatario_id)
    return True


def _laco(parar: threading.Event) -> None:
    import redis

    conexao = redis.Redis.from_url(REDIS_URL, socket_timeout=10, socket_connect_timeout=3)
    while not parar.is_set():
        try:
            item = conexao.brpop([FILA_EVENTOS], timeout=5)  # espera até 5 s por um evento
            if item:
                processar(item[1])
        except redis.RedisError as erro:
            log.warning("Fila indisponível (%s). Tentando de novo...", erro)
            parar.wait(3)
        except Exception:  # um evento com problema não pode parar o consumidor
            log.exception("Erro ao processar evento")


def iniciar() -> threading.Event | None:
    """Inicia o consumidor em segundo plano. Devolve o sinal para parar."""
    if not REDIS_URL:
        log.info("REDIS_URL vazio: consumidor de eventos desligado.")
        return None
    parar = threading.Event()
    threading.Thread(target=_laco, args=(parar,), daemon=True, name="consumidor-eventos").start()
    return parar
