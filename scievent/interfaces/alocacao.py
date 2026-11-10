"""Interface do componente de Alocação de Revisores."""
from __future__ import annotations

from abc import abstractmethod
from typing import Optional

from scievent.interfaces.base import Componente


class IEstrategiaAlocacao(Componente):
    """
    Componente que distribui as submissões entre os revisores.

    Interface fornecida:
        alocar(submissoes, revisores, carga_atual) -> lista de pares

    Um congresso grande aloca por afinidade de tema com 3 revisores; uma
    jornada local faz rodízio com 1 revisor. Por isso a alocação é um hotspot.
    """

    @abstractmethod
    def alocar(
        self,
        submissoes: list[dict],
        revisores: list[dict],
        carga_atual: Optional[dict[int, int]] = None,
    ) -> list[dict]:
        """
        submissoes:  submissões ainda sem revisor
        revisores:   [{"id", "nome", "email", "instituicao", "areas": [..], "palavras_chave": [..]}]
        carga_atual: {revisor_id: quantidade de trabalhos já alocados}
        Retorna [{"submissao_id", "revisor_id", "afinidade"}].
        """
