"""Testes de segurança do serviço de Inventário: ele confere o token sozinho."""
import jwt

from app import config
from tests.conftest import criar_token

ATIVO = {"patrimonio": "PAT-9", "tipo": "outro", "descricao": "X", "setor": "TI"}


def test_rotas_exigem_login(cliente):
    for metodo, rota in [("get", "/ativos"), ("get", "/ativos/1"), ("post", "/ativos")]:
        assert getattr(cliente, metodo)(rota).status_code == 401, rota


def test_solicitante_nao_cadastra_ativo(cliente, contas):
    assert cliente.post("/ativos", headers=contas["ana"]["headers"], json=ATIVO).status_code == 403


def test_token_assinado_com_outro_segredo(cliente):
    falso = criar_token(1, "admin", segredo="segredo-de-outra-pessoa-com-mais-de-32-caracteres")
    assert cliente.post("/ativos", headers={"Authorization": f"Bearer {falso}"}, json=ATIVO).status_code == 401


def test_token_expirado(cliente):
    vencido = criar_token(1, "admin", minutos=-5)
    assert cliente.get("/ativos", headers={"Authorization": f"Bearer {vencido}"}).status_code == 401


def test_token_sem_assinatura_alg_none(cliente):
    falso = jwt.encode({"sub": "1", "perfil": "admin", "iss": config.JWT_EMISSOR, "iat": 0, "exp": 9999999999},
                       None, algorithm="none")
    assert cliente.get("/ativos", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_token_sem_perfil(cliente):
    token = jwt.encode({"sub": "1", "iss": config.JWT_EMISSOR, "iat": 0, "exp": 9999999999},
                       config.JWT_SEGREDO, algorithm="HS256")
    assert cliente.get("/ativos", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_campo_extra_e_recusado(cliente, contas):
    r = cliente.post("/ativos", headers=contas["carla"]["headers"], json={**ATIVO, "id": 50})
    assert r.status_code == 422


def test_patrimonio_com_caracteres_invalidos(cliente, contas):
    r = cliente.post("/ativos", headers=contas["carla"]["headers"], json={**ATIVO, "patrimonio": "<script>"})
    assert r.status_code == 422


def test_cabecalhos_de_seguranca(cliente):
    r = cliente.get("/saude")
    assert r.headers["x-content-type-options"] == "nosniff"
