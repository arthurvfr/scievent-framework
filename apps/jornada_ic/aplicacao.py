"""
APLICAÇÃO 2 — Jornada de Iniciação Científica em Computação (JIC 2026).

Sistema para uma jornada local de iniciação científica, construído reusando
o MESMO framework da Aplicação 1. Muda só a escolha dos componentes: regras
mais simples, um revisor por trabalho, nota única e sala única.

Configuração escolhida em cada hotspot:
    validação     -> ValidadorSimples (resumo até 300 palavras)
    alocação      -> AlocacaoRoundRobin (1 revisor por trabalho)
    formulário    -> FormularioNotaUnica (nota de 0 a 10)
    decisão       -> DecisaoPorNotaMinima (aprovado com nota >= 6)
    programação   -> ProgramacaoSequencial (auditório único, blocos de 3)
    notificação   -> NotificacaoMural
    assistente    -> (gancho não sobrescrito: SemAssistente, sem IA)
    revisão cega  -> não (gancho sobrescrito: o orientador-revisor vê os autores)
"""
from __future__ import annotations

from apps.jornada_ic.dados_exemplo import REVISORES, SUBMISSOES
from scievent.componentes import (
    AlocacaoRoundRobin, DecisaoPorNotaMinima, FormularioNotaUnica, NotificacaoMural,
    ProgramacaoSequencial, ValidadorSimples,
)
from scievent.framework import FrameworkEventoCientifico


class JornadaIniciacaoCientifica(FrameworkEventoCientifico):

    ID_APLICACAO = "jornada"

    # --- HOTSPOT: identidade do evento -----------------------------------
    def definir_evento(self) -> dict:
        return {
            "nome": "Jornada de Iniciação Científica em Computação",
            "sigla": "JIC 2026",
            "descricao": "Apresentação dos projetos de iniciação científica dos estudantes de graduação.",
            "local": "Maceió - AL",
            "data_inicio": "2026-11-27",
            "data_fim": "2026-11-27",
            "trilhas": [
                {"nome": "Computação Aplicada", "palavras_chave": ["aplicativo", "dados", "saúde", "educação"]},
                {"nome": "Sistemas e Redes", "palavras_chave": ["redes", "sensores", "nuvem", "segurança"]},
                {"nome": "Inteligência Artificial", "palavras_chave": ["aprendizado", "modelo", "classificação", "texto"]},
            ],
        }

    # --- HOTSPOTS: componentes mais simples -------------------------------
    def criar_validador(self):
        return ValidadorSimples(max_palavras=300)

    def criar_estrategia_alocacao(self):
        return AlocacaoRoundRobin(revisores_por_trabalho=1)

    def criar_formulario_avaliacao(self):
        return FormularioNotaUnica(minimo=0, maximo=10)

    def criar_politica_decisao(self):
        return DecisaoPorNotaMinima(nota_minima=6.0)

    def criar_gerador_programacao(self):
        return ProgramacaoSequencial(sala="Auditório do Instituto", duracao_min=15, inicio="14:00",
                                     apresentacoes_por_bloco=3, intervalo_min=20, horario_limite="18:00")

    def criar_canal_notificacao(self):
        return NotificacaoMural()

    # --- GANCHO sobrescrito: revisão aberta -------------------------------
    def ocultar_autores_na_revisao(self) -> bool:
        return False

    # --- GANCHO sobrescrito: dados de demonstração ------------------------
    def dados_de_exemplo(self) -> dict:
        return {"revisores": REVISORES, "submissoes": SUBMISSOES}

    # criar_assistente() não é sobrescrito: vale o padrão SemAssistente.
