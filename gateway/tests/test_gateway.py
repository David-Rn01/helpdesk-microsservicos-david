"""Testes do API Gateway, com os serviços simulados (httpx.MockTransport)."""
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main


class Servicos:
    def __init__(self):
        self.fora_do_ar: set[str] = set()
        self.pedidos: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.pedidos.append(request)
        if request.url.host in self.fora_do_ar:
            raise httpx.ConnectError("Connection refused", request=request)
        if request.url.path == "/saude":
            return httpx.Response(200, json={"status": "ok"})
        if "authorization" not in request.headers and request.url.path != "/auth/login":
            return httpx.Response(401, json={"detail": "Faça login para continuar."},
                                  headers={"WWW-Authenticate": "Bearer"})
        return httpx.Response(200, json={"servico": request.url.host, "caminho": request.url.path,
                                          "query": str(request.url.query, "utf-8")})


@pytest.fixture
def servicos(monkeypatch):
    falsos = Servicos()
    monkeypatch.setattr(main, "transporte", httpx.MockTransport(falsos))
    return falsos


@pytest.fixture
def cliente(servicos):
    with TestClient(main.app) as c:
        yield c


H = {"Authorization": "Bearer abc"}


@pytest.mark.parametrize("rota, servico", [
    ("/auth/login", "usuarios"), ("/usuarios/3", "usuarios"), ("/ativos", "inventario"),
    ("/chamados/1/status", "chamados"), ("/chamados/painel", "chamados"), ("/notificacoes", "notificacoes"),
])
def test_encaminha_para_o_servico_certo(cliente, rota, servico):
    r = cliente.get(rota, headers=H)
    assert r.json()["servico"] == servico and r.json()["caminho"] == rota


def test_repassa_token_query_e_corpo(cliente, servicos):
    cliente.patch("/chamados/7/status", headers=H, params={"x": "1"}, json={"status": "resolvido"})
    pedido = servicos.pedidos[-1]
    assert pedido.method == "PATCH" and pedido.headers["authorization"] == "Bearer abc"
    assert pedido.url.query == b"x=1" and b"resolvido" in pedido.content


def test_x_forwarded_for_do_cliente_e_substituido(cliente, servicos):
    cliente.post("/auth/login", headers={"X-Forwarded-For": "1.2.3.4"}, json={})
    assert servicos.pedidos[-1].headers["x-forwarded-for"] != "1.2.3.4"


def test_401_do_servico_chega_na_tela(cliente):
    r = cliente.get("/chamados")
    assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer"


def test_servico_fora_do_ar_da_503(cliente, servicos):
    servicos.fora_do_ar.add("inventario")
    r = cliente.get("/ativos", headers=H)
    assert r.status_code == 503 and "inventário" in r.json()["detail"]
    # os outros continuam funcionando
    assert cliente.get("/chamados", headers=H).status_code == 200


def test_rota_desconhecida(cliente):
    assert cliente.get("/admin/segredos").status_code == 404


def test_saude_mostra_cada_servico(cliente, servicos):
    servicos.fora_do_ar.add("notificacoes")
    r = cliente.get("/saude").json()
    assert r["status"] == "degradado"
    assert r["servicos"]["notificacoes"] == "fora do ar" and r["servicos"]["usuarios"] == "no ar"


def test_tela_e_servida_pelo_gateway(cliente):
    assert "<html" in cliente.get("/").text.lower()
    assert cliente.get("/app.js").headers["content-type"].startswith("text/javascript")
    assert cliente.get("/estilo.css").status_code == 200


def test_cabecalhos_de_seguranca(cliente):
    r = cliente.get("/")
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"


def test_requisicao_grande_demais(cliente):
    r = cliente.post("/chamados", headers={**H, "Content-Type": "application/json"}, content="x" * 70000)
    assert r.status_code == 413


def test_tela_escapa_o_html():
    js = (Path(__file__).parent.parent / "app" / "web" / "app.js").read_text(encoding="utf-8")
    assert "const esc =" in js and "onclick" not in js
