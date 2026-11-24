"""Tratamento de falhas: se Usuários ou Inventário caírem, Chamados responde 503 sem travar."""
from app.eventos import publicador


def abrir(cliente, contas, **extra):
    dados = {"titulo": "PC não liga", "descricao": "Nada acontece", "prioridade": "alta", "ativo_id": 1, **extra}
    return cliente.post("/chamados", headers=contas["ana"]["headers"], json=dados)


def test_inventario_fora_do_ar_da_503_com_mensagem_clara(cliente, contas, servicos):
    servicos.fora_do_ar.add("inventario")
    r = abrir(cliente, contas)
    assert r.status_code == 503
    assert "inventário" in r.json()["detail"] and "fora do ar" in r.json()["detail"]


def test_inventario_lento_da_503(cliente, contas, servicos):
    servicos.lento.add("inventario")
    r = abrir(cliente, contas)
    assert r.status_code == 503 and "demorou" in r.json()["detail"]


def test_chamado_nao_e_gravado_quando_inventario_cai(cliente, contas, servicos):
    servicos.fora_do_ar.add("inventario")
    abrir(cliente, contas)
    assert cliente.get("/chamados", headers=contas["ana"]["headers"]).json() == []


def test_sem_inventario_ainda_abre_chamado_sem_equipamento_e_lista(cliente, contas, servicos):
    servicos.fora_do_ar.add("inventario")
    r = abrir(cliente, contas, ativo_id=None)
    assert r.status_code == 201
    assert len(cliente.get("/chamados", headers=contas["ana"]["headers"]).json()) == 1
    assert cliente.get("/chamados/painel", headers=contas["carla"]["headers"]).status_code == 200


def test_usuarios_fora_do_ar_ao_atribuir_da_503(cliente, contas, servicos):
    cid = abrir(cliente, contas).json()["id"]
    servicos.fora_do_ar.add("usuarios")
    r = cliente.patch(f"/chamados/{cid}/atribuir", headers=contas["carla"]["headers"], json={"tecnico_id": 4})
    assert r.status_code == 503 and "usuários" in r.json()["detail"]
    # o chamado continua como estava
    assert cliente.get(f"/chamados/{cid}", headers=contas["carla"]["headers"]).json()["status"] == "aberto"


def test_fila_fora_do_ar_nao_impede_abrir_chamado(cliente, contas, monkeypatch):
    """Bônus: se a fila (ou o serviço de Notificações) cair, os chamados continuam sendo abertos."""
    monkeypatch.undo()  # volta o publicador verdadeiro
    monkeypatch.setattr(publicador, "REDIS_URL", "redis://endereco-que-nao-existe:6379/0")
    monkeypatch.setattr(publicador, "_conexao", None)
    from app import clientes
    import httpx
    from tests.conftest import OutrosServicos
    monkeypatch.setattr(clientes, "transporte", httpx.MockTransport(OutrosServicos()))
    assert publicador.publicar("ChamadoAberto", 2, "teste") is False
    assert abrir(cliente, contas).status_code == 201
