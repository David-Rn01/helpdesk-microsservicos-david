import os

# Precisa vir antes de importar o app: o config exige o segredo
os.environ.setdefault("JWT_SEGREDO", "segredo-so-para-testes-com-mais-de-32-caracteres")
os.environ["DADOS_EXEMPLO"] = "0"
os.environ["REDIS_URL"] = ""

from datetime import datetime, timedelta, timezone  # noqa: E402

import httpx  # noqa: E402
import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import clientes, config  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.eventos import publicador  # noqa: E402
from app.main import app  # noqa: E402

# Usuários e ativos que os serviços "falsos" conhecem
USUARIOS = {1: "admin", 2: "solicitante", 3: "solicitante", 4: "tecnico"}
ATIVOS = {1: "PAT-1"}


def criar_token(usuario_id: int, perfil: str, segredo: str | None = None, minutos: int = 60) -> str:
    """Gera um token igual ao que o serviço de Usuários cria no login."""
    agora = datetime.now(timezone.utc)
    dados = {"sub": str(usuario_id), "perfil": perfil, "iss": config.JWT_EMISSOR,
             "iat": agora, "exp": agora + timedelta(minutes=minutos)}
    return jwt.encode(dados, segredo or config.JWT_SEGREDO, algorithm="HS256")


class OutrosServicos:
    """Simula os serviços de Usuários e Inventário (httpx.MockTransport)."""

    def __init__(self):
        self.fora_do_ar: set[str] = set()   # "usuarios" e/ou "inventario"
        self.lento: set[str] = set()
        self.chamadas: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.chamadas.append(request)
        servico = request.url.host
        if servico in self.fora_do_ar:
            raise httpx.ConnectError("Connection refused", request=request)
        if servico in self.lento:
            raise httpx.ReadTimeout("timed out", request=request)
        if not request.headers.get("authorization", "").startswith("Bearer "):
            return httpx.Response(401, json={"detail": "Faça login para continuar."})
        partes = request.url.path.strip("/").split("/")
        if servico == "usuarios" and partes[0] == "usuarios" and int(partes[1]) in USUARIOS:
            uid = int(partes[1])
            return httpx.Response(200, json={"id": uid, "nome": f"Usuário {uid}", "perfil": USUARIOS[uid]})
        if servico == "inventario" and partes[0] == "ativos" and int(partes[1]) in ATIVOS:
            aid = int(partes[1])
            return httpx.Response(200, json={"id": aid, "patrimonio": ATIVOS[aid], "tipo": "computador",
                                             "descricao": "Desktop", "setor": "TI"})
        return httpx.Response(404, json={"detail": "não encontrado"})


@pytest.fixture
def servicos(monkeypatch):
    falsos = OutrosServicos()
    monkeypatch.setattr(clientes, "transporte", httpx.MockTransport(falsos))
    return falsos


@pytest.fixture
def eventos(monkeypatch):
    """Guarda os eventos publicados em vez de mandar para o Redis."""
    publicados = []
    monkeypatch.setattr(publicador, "publicar",
                        lambda tipo, destinatario_id, mensagem: publicados.append((tipo, destinatario_id)) or True)
    return publicados


@pytest.fixture
def cliente(servicos, eventos):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def db_de_teste():
        db = Sessao()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = db_de_teste
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def contas():
    apelidos = {"admin": 1, "ana": 2, "bia": 3, "carla": 4}
    return {apelido: {"id": i, "headers": {"Authorization": f"Bearer {criar_token(i, USUARIOS[i])}"}}
            for apelido, i in apelidos.items()}


@pytest.fixture
def ativo():
    return {"id": 1}
