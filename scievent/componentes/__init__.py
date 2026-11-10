"""
Biblioteca de componentes prontos do SciEvent.

Uma aplicação pode usar qualquer um destes componentes nos hotspots do
framework, ou escrever o seu próprio, desde que implemente a interface.
"""
from scievent.componentes.alocacao import AlocacaoPorAfinidade, AlocacaoRoundRobin
from scievent.componentes.assistente import AssistenteAgentes, SemAssistente
from scievent.componentes.decisao import DecisaoPorMediaPonderada, DecisaoPorNotaMinima
from scievent.componentes.formularios import CRITERIOS_PADRAO, FormularioNotaUnica, FormularioPonderado
from scievent.componentes.notificacao import NotificacaoEmail, NotificacaoMural
from scievent.componentes.programacao import ProgramacaoPorTrilhas, ProgramacaoSequencial
from scievent.componentes.validacao import ValidadorRigoroso, ValidadorSimples

__all__ = [
    "ValidadorRigoroso", "ValidadorSimples",
    "AlocacaoPorAfinidade", "AlocacaoRoundRobin",
    "FormularioPonderado", "FormularioNotaUnica", "CRITERIOS_PADRAO",
    "DecisaoPorMediaPonderada", "DecisaoPorNotaMinima",
    "ProgramacaoPorTrilhas", "ProgramacaoSequencial",
    "NotificacaoEmail", "NotificacaoMural",
    "AssistenteAgentes", "SemAssistente",
]
