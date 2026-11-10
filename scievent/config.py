"""
Configuração central do SciEvent: portas, endereços e pastas.

Todas as portas podem ser trocadas por variável de ambiente, sem mexer no
código. Exemplo (PowerShell):  $env:SCIEVENT_PORTA_GATEWAY = "8000"
"""
from __future__ import annotations

import os

# Usamos 127.0.0.1 em vez de "localhost" de propósito: no Windows, "localhost"
# tenta IPv6 primeiro e cada chamada entre serviços pode atrasar ~2 segundos.
HOST = os.environ.get("SCIEVENT_HOST", "127.0.0.1")

# Porta padrão de cada processo do sistema.
PORTAS: dict[str, int] = {
    "gateway": 5000,       # API Gateway + interface web
    "eventos": 5001,       # cadastro do evento, trilhas e componentes em uso
    "submissoes": 5002,    # trabalhos submetidos pelos autores
    "revisoes": 5003,      # revisores, alocações e avaliações
    "programacao": 5004,   # grade de sessões do evento
    "notificacoes": 5005,  # mensagens enviadas (e-mail simulado ou mural)
    "agentes": 5006,       # agentes de IA (opcional)
    "registro": 5010,      # Service Registry (descoberta de serviços)
}

# Ordem em que o lançador sobe os processos (o registro vem primeiro).
ORDEM_INICIALIZACAO = [
    "registro", "eventos", "submissoes", "revisoes",
    "programacao", "notificacoes", "agentes", "gateway",
]

PASTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DADOS = os.environ.get("SCIEVENT_DADOS", os.path.join(PASTA_RAIZ, "data"))
PASTA_LOGS = os.path.join(PASTA_RAIZ, "logs")

# Intervalo (s) entre heartbeats enviados ao registro e tempo (s) sem
# heartbeat a partir do qual o registro considera o serviço fora do ar.
INTERVALO_HEARTBEAT = 5
TEMPO_EXPIRACAO = 15

# Tempo máximo (s) de espera de uma chamada HTTP entre serviços.
TIMEOUT_HTTP = float(os.environ.get("SCIEVENT_TIMEOUT", "10"))


def porta(nome: str) -> int:
    """Porta do serviço `nome`, respeitando SCIEVENT_PORTA_<NOME> se definida."""
    return int(os.environ.get(f"SCIEVENT_PORTA_{nome.upper()}", PORTAS[nome]))


def url_padrao(nome: str) -> str:
    """Endereço fixo do serviço, usado quando o registro não responde."""
    return os.environ.get(f"SCIEVENT_{nome.upper()}_URL", f"http://{HOST}:{porta(nome)}")
