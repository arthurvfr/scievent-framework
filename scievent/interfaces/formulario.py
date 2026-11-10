"""Interface do componente de Formulário de Avaliação."""
from __future__ import annotations

from abc import abstractmethod

from scievent.interfaces.base import Componente
from scievent.modelos import Criterio


class IFormularioAvaliacao(Componente):
    """
    Componente que define o que o revisor preenche e como vira uma nota.

    Interface fornecida:
        criterios()                      -> critérios exibidos no formulário
        validar(respostas, comentario)   -> lista de erros
        calcular_nota(respostas)         -> nota final da revisão

    A interface web monta o formulário a partir de criterios(); o núcleo
    nunca conhece os critérios de antemão.
    """

    @abstractmethod
    def criterios(self) -> list[Criterio]:
        """Critérios na ordem em que aparecem no formulário."""

    @abstractmethod
    def validar(self, respostas: dict[str, float], comentario: str) -> list[str]:
        """respostas: {chave_do_criterio: valor}"""

    @abstractmethod
    def calcular_nota(self, respostas: dict[str, float]) -> float:
        """Nota única da revisão, na escala do formulário."""
