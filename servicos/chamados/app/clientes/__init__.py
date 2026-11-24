"""Clientes HTTP para os outros serviços.

Toda chamada:
- usa tempo limite (TIMEOUT_SEGUNDOS), para não travar se o outro serviço sumir;
- repassa o token do usuário no cabeçalho Authorization;
- transforma falha de rede em ServicoIndisponivel (resposta 503).
"""
import logging

import httpx

from app.config import TIMEOUT_SEGUNDOS
from app.erros import NaoEncontrado, ServicoIndisponivel

log = logging.getLogger("chamados.clientes")

# Os testes trocam por um httpx.MockTransport para simular os outros serviços
transporte: httpx.BaseTransport | None = None


def buscar(url_base: str, caminho: str, token: str, servico: str, nao_encontrado: str) -> dict:
    try:
        with httpx.Client(base_url=url_base, timeout=TIMEOUT_SEGUNDOS, transport=transporte) as cliente:
            resposta = cliente.get(caminho, headers={"Authorization": f"Bearer {token}"})
    except httpx.TimeoutException:
        log.warning("Tempo esgotado ao chamar %s%s", url_base, caminho)
        raise ServicoIndisponivel(f"O serviço de {servico} demorou demais para responder. Tente de novo em instantes.")
    except httpx.HTTPError:
        log.warning("Falha de rede ao chamar %s%s", url_base, caminho)
        raise ServicoIndisponivel(f"O serviço de {servico} está fora do ar. Tente de novo em instantes.")

    if resposta.status_code == 404:
        raise NaoEncontrado(nao_encontrado)
    if resposta.status_code != 200:
        log.warning("Resposta %s de %s%s", resposta.status_code, url_base, caminho)
        raise ServicoIndisponivel(f"O serviço de {servico} não conseguiu responder agora.")
    return resposta.json()
