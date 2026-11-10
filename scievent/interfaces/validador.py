"""Interface do componente de Validação de Submissão."""
from __future__ import annotations

from abc import abstractmethod

from scievent.interfaces.base import Componente


class IValidadorSubmissao(Componente):
    """
    Componente que decide se uma submissão atende às regras do evento.

    Interface fornecida:
        validar(submissao, evento) -> lista de erros (vazia = válida)

    Cada evento tem regras próprias (tamanho do resumo, número de palavras-chave,
    anonimato...). Por isso a validação é um hotspot.
    """

    @abstractmethod
    def validar(self, submissao: dict, evento: dict) -> list[str]:
        """
        submissao: {"titulo", "resumo", "palavras_chave": [..], "trilha",
                    "autores": [{"nome", "email", "instituicao"}]}
        evento:    registro do evento (inclui "trilhas")
        Retorna uma lista de mensagens de erro legíveis pelo autor.
        """
