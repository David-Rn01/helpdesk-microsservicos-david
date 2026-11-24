import json

import jwt

from app import config, consumidor
from tests.conftest import criar_token


def evento(tipo, destinatario_id, mensagem="Aviso"):
    return json.dumps({"tipo": tipo, "destinatario_id": destinatario_id, "mensagem": mensagem})


def test_saude(cliente):
    assert cliente.get("/saude").json()["status"] == "ok"


def test_evento_vira_notificacao(cliente, contas):
    assert consumidor.processar(evento("ChamadoAberto", 2, "Seu chamado #1 foi aberto."))
    avisos = cliente.get("/notificacoes", headers=contas["ana"]["headers"]).json()
    assert avisos[0]["tipo"] == "ChamadoAberto" and avisos[0]["mensagem"] == "Seu chamado #1 foi aberto."


def test_os_tres_eventos_sao_aceitos(cliente, contas):
    for tipo in ("ChamadoAberto", "ChamadoAtribuido", "ChamadoResolvido"):
        assert consumidor.processar(evento(tipo, 4))
    assert len(cliente.get("/notificacoes", headers=contas["carla"]["headers"]).json()) == 3


def test_evento_invalido_e_ignorado(cliente, contas):
    assert not consumidor.processar("isto não é json")
    assert not consumidor.processar(json.dumps({"tipo": "ChamadoAberto"}))
    assert not consumidor.processar(evento("ApagarTudo", 2))
    assert cliente.get("/notificacoes", headers=contas["ana"]["headers"]).json() == []


def test_notificacoes_sao_so_do_proprio_usuario(cliente, contas):
    consumidor.processar(evento("ChamadoAberto", 2))
    assert cliente.get("/notificacoes", headers=contas["bia"]["headers"]).json() == []


def test_exige_login(cliente):
    assert cliente.get("/notificacoes").status_code == 401


def test_token_assinado_com_outro_segredo(cliente):
    falso = criar_token(2, "solicitante", segredo="segredo-de-outra-pessoa-com-mais-de-32-caracteres")
    assert cliente.get("/notificacoes", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_token_sem_assinatura_alg_none(cliente):
    falso = jwt.encode({"sub": "2", "perfil": "solicitante", "iss": config.JWT_EMISSOR, "iat": 0, "exp": 9999999999},
                       None, algorithm="none")
    assert cliente.get("/notificacoes", headers={"Authorization": f"Bearer {falso}"}).status_code == 401
