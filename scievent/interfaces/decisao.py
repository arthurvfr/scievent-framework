"""Interface do componente de Política de Decisão."""
from __future__ import annotations

from abc import abstractmethod

from scievent.interfaces.base import Componente
from scievent.modelos import Decisao


class IPoliticaDecisao(Componente):
    """
    Componente que transforma as notas das revisões em aceite ou rejeição.

    Interface fornecida:
        decidir(submissao, notas) -> Decisao(status, modalidade, media, justificativa)
    """

    @abstractmethod
    def decidir(self, submissao: dict, notas: list[float]) -> Decisao:
        """notas: nota final de cada revisão recebida pela submissão."""
