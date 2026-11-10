"""Interface do componente de Canal de Notificação."""
from __future__ import annotations

from abc import abstractmethod

from scievent.interfaces.base import Componente
from scievent.modelos import Mensagem

# Tipos de notificação que o núcleo do framework emite.
TIPOS_NOTIFICACAO = (
    "submissao_recebida",     # contexto: evento, titulo, id
    "convite_revisao",        # contexto: evento, nome, quantidade
    "decisao",                # contexto: evento, titulo, status, modalidade, media
    "programacao_publicada",  # contexto: evento, sessoes
)


class ICanalNotificacao(Componente):
    """
    Componente que define por onde e com que texto os participantes são avisados.

    Interface fornecida:
        canal                      -> nome do canal ("email", "mural"...)
        formatar(tipo, contexto)   -> Mensagem(assunto, corpo)

    O envio em si é feito pelo microsserviço de notificações; o componente
    só decide o canal e o texto.
    """

    @property
    @abstractmethod
    def canal(self) -> str:
        """Identificador do canal gravado junto com a notificação."""

    @abstractmethod
    def formatar(self, tipo: str, contexto: dict) -> Mensagem:
        """tipo: um de TIPOS_NOTIFICACAO."""
