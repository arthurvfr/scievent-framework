"""Implementações do componente Assistente de IA."""
from __future__ import annotations

import logging
from typing import Optional

from scievent.clientes import ClienteAgentes, ErroServico
from scievent.interfaces import IAssistente
from scievent.modelos import Decisao

log = logging.getLogger("scievent.assistente")


class SemAssistente(IAssistente):
    """Null Object: a aplicação não usa IA e o fluxo segue sem esta etapa."""

    def descricao(self) -> str:
        return "Nenhum assistente de IA"

    def triar(self, submissao, evento):
        return None

    def meta_revisao(self, submissao, revisoes, decisao, evento):
        return None


class AssistenteAgentes(IAssistente):
    """
    Delega a triagem e a meta-revisão ao microsserviço de agentes, onde agentes
    com papéis definidos trocam mensagens estruturadas por um pool compartilhado
    (inspirado no MetaGPT). Se o microsserviço estiver fora do ar, devolve None
    e o fluxo principal continua (degradação graciosa).
    """

    def __init__(self, cliente: ClienteAgentes):
        self.cliente = cliente

    def descricao(self) -> str:
        return "Agentes de Triagem e de Meta-revisão via pool de mensagens"

    def triar(self, submissao, evento) -> Optional[dict]:
        try:
            return self.cliente.triagem(evento, submissao)
        except ErroServico as erro:
            log.warning("Triagem por IA indisponível: %s", erro)
            return None

    def meta_revisao(self, submissao, revisoes, decisao: Decisao, evento) -> Optional[str]:
        try:
            resposta = self.cliente.meta_revisao(evento, submissao, revisoes, decisao.como_dict())
            return resposta.get("texto")
        except ErroServico as erro:
            log.warning("Meta-revisão por IA indisponível: %s", erro)
            return None
