ATIVO = {"patrimonio": "PAT-1", "tipo": "computador", "descricao": "Desktop", "setor": "TI"}


def test_saude(cliente):
    assert cliente.get("/saude").json()["status"] == "ok"


def test_tecnico_cadastra_ativo_e_filtra_por_setor(cliente, contas):
    h = contas["carla"]["headers"]
    cliente.post("/ativos", headers=h, json={"patrimonio": "PAT-1", "tipo": "impressora", "descricao": "HP", "setor": "RH"})
    cliente.post("/ativos", headers=h, json={"patrimonio": "PAT-2", "tipo": "computador", "descricao": "Dell", "setor": "TI"})
    assert len(cliente.get("/ativos", params={"setor": "RH"}, headers=h).json()) == 1


def test_admin_cadastra_ativo(cliente, contas):
    assert cliente.post("/ativos", headers=contas["admin"]["headers"], json=ATIVO).status_code == 201


def test_obter_ativo_por_id(cliente, contas):
    """Rota usada pelo serviço de Chamados para conferir o equipamento."""
    criado = cliente.post("/ativos", headers=contas["carla"]["headers"], json=ATIVO).json()
    r = cliente.get(f"/ativos/{criado['id']}", headers=contas["ana"]["headers"])
    assert r.status_code == 200 and r.json()["patrimonio"] == "PAT-1"


def test_ativo_inexistente(cliente, contas):
    assert cliente.get("/ativos/999", headers=contas["ana"]["headers"]).status_code == 404


def test_patrimonio_repetido(cliente, contas):
    h = contas["carla"]["headers"]
    cliente.post("/ativos", headers=h, json=ATIVO)
    assert cliente.post("/ativos", headers=h, json=ATIVO).status_code == 422
