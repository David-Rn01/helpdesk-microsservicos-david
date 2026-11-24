"""Configurações do API Gateway (lidas das variáveis de ambiente)."""
import os

USUARIOS_URL = os.getenv("USUARIOS_URL", "http://usuarios:8000")
INVENTARIO_URL = os.getenv("INVENTARIO_URL", "http://inventario:8000")
CHAMADOS_URL = os.getenv("CHAMADOS_URL", "http://chamados:8000")
NOTIFICACOES_URL = os.getenv("NOTIFICACOES_URL", "http://notificacoes:8000")

# Primeiro trecho da rota -> (nome do serviço para as mensagens, endereço)
ROTAS = {
    "auth": ("usuários", USUARIOS_URL),
    "usuarios": ("usuários", USUARIOS_URL),
    "ativos": ("inventário", INVENTARIO_URL),
    "chamados": ("chamados", CHAMADOS_URL),
    "notificacoes": ("notificações", NOTIFICACOES_URL),
}

SERVICOS = {
    "usuarios": USUARIOS_URL,
    "inventario": INVENTARIO_URL,
    "chamados": CHAMADOS_URL,
    "notificacoes": NOTIFICACOES_URL,
}

# Tempo máximo de espera por um serviço, em segundos
TIMEOUT_SEGUNDOS = float(os.getenv("TIMEOUT_SEGUNDOS", "5"))

# Tamanho máximo do corpo de uma requisição (em bytes)
TAMANHO_MAXIMO_REQUISICAO = 64 * 1024
