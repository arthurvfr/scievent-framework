"""Interface do componente Assistente de IA (opcional)."""
from __future__ import annotations

from abc import abstractmethod
from typing import Optional

from scievent.interfaces.base import Componente
from scievent.modelos import Decisao


class IAssistente(Componente):
    """
    Componente que apoia a comissão com agentes de IA.

    Interface fornecida:
        triar(submissao, evento)                          -> parecer de triagem ou None
        meta_revisao(submissao, revisoes, decisao, evento) -> texto consolidado ou None

    Devolver None significa "sem contribuição": o fluxo do framework segue
    normalmente. É por isso que o hotspot é opcional (gancho com padrão).
    """

    @abstractmethod
    def triar(self, submissao: dict, evento: dict) -> Optional[dict]:
        """Sugere trilha e palavras-chave e aponta problemas da submissão."""

    @abstractmethod
    def meta_revisao(
        self, submissao: dict, revisoes: list[dict], decisao: Decisao, evento: dict
    ) -> Optional[str]:
        """Redige o parecer consolidado a partir das revisões recebidas."""
