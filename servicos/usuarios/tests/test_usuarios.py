import jwt

from app import config


def test_saude(cliente):
    assert cliente.get("/saude").json()["status"] == "ok"


def test_login_devolve_token_com_id_e_perfil(cliente, contas):
    """Os outros serviços leem o id e o perfil direto do token."""
    token = contas["carla"]["headers"]["Authorization"].split()[1]
    dados = jwt.decode(token, config.JWT_SEGREDO, algorithms=["HS256"], issuer=config.JWT_EMISSOR)
    assert dados["sub"] == str(contas["carla"]["id"]) and dados["perfil"] == "tecnico"


def test_admin_cria_usuario(cliente, contas):
    r = cliente.post("/usuarios", headers=contas["admin"]["headers"],
                     json={"nome": "Davi", "email": "davi@x.com", "perfil": "tecnico", "senha": "Forte1234"})
    assert r.status_code == 201
    assert "senha" not in r.json() and "senha_hash" not in r.json()


def test_email_repetido_e_recusado(cliente, contas):
    dados = {"nome": "Ana 2", "email": "ANA@x.com", "perfil": "solicitante", "senha": "Forte1234"}
    assert cliente.post("/usuarios", headers=contas["admin"]["headers"], json=dados).status_code == 422


def test_usuario_inexistente(cliente, contas):
    assert cliente.get("/usuarios/99", headers=contas["ana"]["headers"]).status_code == 404


def test_obter_usuario_mostra_perfil_sem_email(cliente, contas):
    """Rota usada pelo serviço de Chamados para conferir o técnico."""
    r = cliente.get(f"/usuarios/{contas['carla']['id']}", headers=contas["ana"]["headers"]).json()
    assert r["perfil"] == "tecnico" and "email" not in r


def test_lista_publica_nao_mostra_email(cliente, contas):
    lista = cliente.get("/usuarios", headers=contas["ana"]["headers"]).json()
    assert lista and all("email" not in u for u in lista)


def test_eu(cliente, contas):
    r = cliente.get("/auth/eu", headers=contas["ana"]["headers"]).json()
    assert r["email"] == "ana@x.com"
