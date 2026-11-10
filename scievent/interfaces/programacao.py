"""Interface do componente de Geração de Programação."""
from __future__ import annotations

from abc import abstractmethod

from scievent.interfaces.base import Componente
from scievent.modelos import Programa


class IGeradorProgramacao(Componente):
    """
    Componente que monta a grade do evento a partir dos trabalhos aceitos.

    Interface fornecida:
        gerar(aceitos, evento, tentativa) -> Programa
        verificar_conflitos(programa)     -> lista de conflitos (vazia = ok)

    O núcleo chama gerar() e verificar_conflitos() em laço: se houver conflito
    (ex.: um autor apresentando em duas salas no mesmo horário), pede uma nova
    tentativa. O número da tentativa permite ao componente variar a grade.
    """

    @abstractmethod
    def gerar(self, aceitos: list[dict], evento: dict, tentativa: int) -> Programa:
        """aceitos: submissões com status 'aceito' (cada uma traz 'decisao')."""

    @abstractmethod
    def verificar_conflitos(self, programa: Programa) -> list[str]:
        """Mensagens descrevendo cada conflito encontrado."""
