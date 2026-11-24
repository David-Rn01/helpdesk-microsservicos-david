import os

# Precisa vir antes de importar o app: o config exige o segredo
os.environ.setdefault("JWT_SEGREDO", "segredo-so-para-testes-com-mais-de-32-caracteres")
os.environ["REDIS_URL"] = ""  # nos testes, os eventos são entregues direto ao consumidor

from datetime import datetime, timedelta, timezone  # noqa: E402

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import config, consumidor  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


def criar_token(usuario_id: int, perfil: str, segredo: str | None = None, minutos: int = 60) -> str:
    agora = datetime.now(timezone.utc)
    dados = {"sub": str(usuario_id), "perfil": perfil, "iss": config.JWT_EMISSOR,
             "iat": agora, "exp": agora + timedelta(minutes=minutos)}
    return jwt.encode(dados, segredo or config.JWT_SEGREDO, algorithm="HS256")


@pytest.fixture
def cliente(monkeypatch):
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
    monkeypatch.setattr(consumidor, "SessionLocal", Sessao)  # o consumidor grava no mesmo banco de teste
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def contas():
    return {apelido: {"id": i, "headers": {"Authorization": f"Bearer {criar_token(i, p)}"}}
            for apelido, (i, p) in {"ana": (2, "solicitante"), "bia": (3, "solicitante"), "carla": (4, "tecnico")}.items()}
