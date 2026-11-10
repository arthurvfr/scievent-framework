"""
Objetos de valor trocados entre o núcleo do framework e os componentes.

São estruturas simples (dataclasses) que os componentes devolvem ao núcleo.
Os dados de domínio persistidos (evento, submissão, revisor, revisão) trafegam
como dicionários JSON vindos dos microsserviços.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class Criterio:
    """Um critério do formulário de avaliação (ex.: Originalidade, peso 0,3, nota 1 a 5)."""
    chave: str
    rotulo: str
    peso: float = 1.0
    minimo: int = 1
    maximo: int = 5
    ajuda: str = ""


@dataclass
class Decisao:
    """Resultado da política de decisão para uma submissão."""
    status: str                      # "aceito" ou "rejeitado"
    modalidade: Optional[str]        # "oral", "poster" ou None
    media: float
    justificativa: str

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Mensagem:
    """Notificação já formatada pelo canal (assunto e corpo)."""
    assunto: str
    corpo: str


@dataclass
class Apresentacao:
    """Um trabalho dentro de uma sessão da programação."""
    submissao_id: int
    titulo: str
    autores: str
    autores_emails: list[str]
    trilha: str
    inicio: str
    fim: str


@dataclass
class Sessao:
    """Uma sessão da programação: sala, horário e apresentações."""
    titulo: str
    sala: str
    inicio: str
    fim: str
    trilha: str
    apresentacoes: list[Apresentacao] = field(default_factory=list)


@dataclass
class Programa:
    """Programação gerada pelo componente de programação."""
    sessoes: list[Sessao]
    observacoes: list[str] = field(default_factory=list)

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResultadoSubmissao:
    """Retorno do template method submeter_trabalho()."""
    aceita: bool
    erros: list[str] = field(default_factory=list)
    submissao: Optional[dict] = None


@dataclass
class ResultadoRevisao:
    """Retorno do template method registrar_revisao()."""
    registrada: bool
    erros: list[str] = field(default_factory=list)
    revisao: Optional[dict] = None


def minutos(hhmm: str) -> int:
    """'09:30' -> 570"""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def hhmm(total_minutos: int) -> str:
    """570 -> '09:30'"""
    return f"{total_minutos // 60:02d}:{total_minutos % 60:02d}"
