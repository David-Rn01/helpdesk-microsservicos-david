"""Cria os equipamentos de exemplo quando o banco está vazio (só para aula)."""
from sqlalchemy.orm import Session

from app.inventario import servico as inventario
from app.inventario.esquemas import AtivoCriar

ATIVOS = [
    ("PAT-0001", "computador", "Desktop Dell OptiPlex", "Financeiro"),   # id 1
    ("PAT-0002", "impressora", "Impressora HP LaserJet", "RH"),          # id 2
    ("PAT-0003", "notebook", "Notebook Lenovo ThinkPad", "TI"),          # id 3
]


def carregar(db: Session) -> None:
    if inventario.listar(db):
        return
    for patrimonio, tipo, descricao, setor in ATIVOS:
        inventario.criar(db, AtivoCriar(patrimonio=patrimonio, tipo=tipo, descricao=descricao, setor=setor))
