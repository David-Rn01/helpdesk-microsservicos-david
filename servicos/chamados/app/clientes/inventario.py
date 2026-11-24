"""Chamadas HTTP ao serviço de Inventário."""
from app.clientes import buscar
from app.config import INVENTARIO_URL


def obter_ativo(ativo_id: int, token: str) -> dict:
    """GET /ativos/{id}: confere se o equipamento existe."""
    return buscar(INVENTARIO_URL, f"/ativos/{ativo_id}", token, "inventário",
                  f"Ativo {ativo_id} não encontrado.")
