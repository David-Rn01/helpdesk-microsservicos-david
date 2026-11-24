"""Cria chamados de exemplo quando o banco está vazio (só para aula).

Usa os ids fixos dos dados de exemplo dos outros serviços:
Ana = 2, Bruno = 3, Carla = 4; computador = 1, impressora = 2.
Não chama os outros serviços, porque eles podem ainda estar subindo.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.chamados import repositorio
from app.chamados.modelos import Chamado
from app.chamados.servico import calcular_prazo

ANA, BRUNO, CARLA = 2, 3, 4
COMPUTADOR, IMPRESSORA = 1, 2


def carregar(db: Session) -> None:
    if repositorio.listar(db):
        return
    agora = datetime.now()
    exemplos = [
        ("Computador não liga", "Apertei o botão e nada acontece.", "alta", COMPUTADOR, ANA, CARLA, "em_atendimento"),
        ("Impressora atolando papel", "Atola a cada 3 folhas.", "media", IMPRESSORA, BRUNO, None, "aberto"),
        ("Acesso ao sistema de RH", "Preciso de acesso para a nova estagiária.", "baixa", None, BRUNO, None, "aberto"),
    ]
    for titulo, descricao, prioridade, ativo_id, solicitante_id, tecnico_id, status in exemplos:
        repositorio.salvar(db, Chamado(
            titulo=titulo, descricao=descricao, prioridade=prioridade, ativo_id=ativo_id,
            solicitante_id=solicitante_id, tecnico_id=tecnico_id, status=status,
            criado_em=agora, prazo_sla=calcular_prazo(prioridade, agora),
        ))
