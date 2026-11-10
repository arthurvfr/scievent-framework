"""Superclasse comum a todos os componentes plugáveis do framework."""
from __future__ import annotations

from abc import ABC, abstractmethod


class Componente(ABC):
    """
    Todo componente do SciEvent sabe dizer seu nome e o que faz.

    O núcleo usa essas duas informações para registrar, no microsserviço de
    eventos, quais componentes a aplicação plugou em cada hotspot. Assim a
    interface web mostra, para cada evento, a configuração em uso.
    """

    @property
    def nome(self) -> str:
        return type(self).__name__

    @abstractmethod
    def descricao(self) -> str:
        """Frase curta explicando a regra que este componente aplica."""
