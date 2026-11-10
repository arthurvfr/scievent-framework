"""
Interfaces (contratos) dos componentes do SciEvent.

Cada interface corresponde a um hotspot do framework. Uma aplicação escolhe,
para cada uma, qual implementação usar.
"""
from scievent.interfaces.alocacao import IEstrategiaAlocacao
from scievent.interfaces.assistente import IAssistente
from scievent.interfaces.base import Componente
from scievent.interfaces.decisao import IPoliticaDecisao
from scievent.interfaces.formulario import IFormularioAvaliacao
from scievent.interfaces.notificacao import TIPOS_NOTIFICACAO, ICanalNotificacao
from scievent.interfaces.programacao import IGeradorProgramacao
from scievent.interfaces.validador import IValidadorSubmissao

__all__ = [
    "Componente",
    "IValidadorSubmissao",
    "IEstrategiaAlocacao",
    "IFormularioAvaliacao",
    "IPoliticaDecisao",
    "IGeradorProgramacao",
    "ICanalNotificacao",
    "IAssistente",
    "TIPOS_NOTIFICACAO",
]
