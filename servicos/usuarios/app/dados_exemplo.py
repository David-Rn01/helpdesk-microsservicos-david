"""Cria os usuários de exemplo quando o banco está vazio (só para aula).

Os ids ficam fixos (1 a 5) porque os dados de exemplo dos serviços de Inventário
e Chamados se referem a eles. Em produção, rode com DADOS_EXEMPLO=0.
"""
import os

from sqlalchemy.orm import Session

from app.usuarios import servico as usuarios
from app.usuarios.esquemas import UsuarioCriar

SENHA = os.getenv("SENHA_EXEMPLO", "Helpdesk2026")

CONTAS = [
    ("Admin TI", "admin@empresa.com", "admin"),        # id 1
    ("Ana Souza", "ana@empresa.com", "solicitante"),   # id 2
    ("Bruno Lima", "bruno@empresa.com", "solicitante"),  # id 3
    ("Carla Dias", "carla@empresa.com", "tecnico"),    # id 4
    ("Diego Rocha", "diego@empresa.com", "tecnico"),   # id 5
]


def carregar(db: Session) -> None:
    if usuarios.listar(db):
        return
    for nome, email, perfil in CONTAS:
        usuarios.criar(db, UsuarioCriar(nome=nome, email=email, perfil=perfil, senha=SENHA))
