"""Configurações do serviço de inventario (lidas das variáveis de ambiente)."""
import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventario.db")


def _ler_segredo() -> str:
    """O segredo vem do .env (JWT_SEGREDO) ou do arquivo gerado pelo docker compose.

    Todos os serviços precisam do MESMO segredo; por isso não há valor padrão no código.
    """
    segredo = os.getenv("JWT_SEGREDO", "")
    if len(segredo) < 32:
        arquivo = Path(os.getenv("JWT_SEGREDO_ARQUIVO", "/segredos/jwt"))
        if arquivo.is_file():
            segredo = arquivo.read_text().strip()
    if len(segredo) < 32:
        raise RuntimeError("Defina JWT_SEGREDO no .env (mínimo de 32 caracteres).")
    return segredo


JWT_SEGREDO = _ler_segredo()
JWT_ALGORITMO = "HS256"
JWT_EMISSOR = "helpdesk-ti"

# Tamanho máximo do corpo de uma requisição (em bytes)
TAMANHO_MAXIMO_REQUISICAO = 64 * 1024

DOCS_ATIVA = os.getenv("DOCS", "1") == "1"
