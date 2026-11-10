"""
APLICAÇÃO 1 — Congresso Brasileiro de Computação Aplicada (CBCA 2026).

Sistema para um congresso nacional de grande porte, construído reusando o
framework SciEvent. Só os hotspots são implementados aqui; todo o fluxo
(submissão, revisão, decisão, programação, notificação) vem do framework.

Configuração escolhida em cada hotspot:
    validação     -> ValidadorRigoroso (resumo 50-300 palavras, 3-5 palavras-chave, anonimato)
    alocação      -> AlocacaoPorAfinidade (3 revisores por trabalho, sem conflito de interesse)
    formulário    -> FormularioPonderado (4 critérios com pesos, nota de 1 a 5)
    decisão       -> DecisaoPorMediaPonderada (oral >= 3,5; pôster >= 3,0)
    programação   -> ProgramacaoPorTrilhas (3 salas paralelas)
    notificação   -> NotificacaoEmail
    assistente    -> AssistenteAgentes (gancho sobrescrito: usa IA)
"""
from __future__ import annotations

from apps.congresso_nacional.dados_exemplo import REVISORES, SUBMISSOES
from scievent.componentes import (
    AlocacaoPorAfinidade, AssistenteAgentes, DecisaoPorMediaPonderada, FormularioPonderado,
    NotificacaoEmail, ProgramacaoPorTrilhas, ValidadorRigoroso,
)
from scievent.framework import FrameworkEventoCientifico


class CongressoNacional(FrameworkEventoCientifico):

    ID_APLICACAO = "congresso"

    # --- HOTSPOT: identidade do evento -----------------------------------
    def definir_evento(self) -> dict:
        return {
            "nome": "Congresso Brasileiro de Computação Aplicada",
            "sigla": "CBCA 2026",
            "descricao": "Congresso nacional com revisão por pares duplo-cega e sessões técnicas paralelas.",
            "local": "Maceió - AL",
            "data_inicio": "2026-12-07",
            "data_fim": "2026-12-09",
            "trilhas": [
                {"nome": "Inteligência Artificial",
                 "palavras_chave": ["aprendizado de máquina", "redes neurais", "modelos de linguagem",
                                    "visão computacional", "agentes", "classificação"]},
                {"nome": "Engenharia de Software",
                 "palavras_chave": ["microsserviços", "reuso", "frameworks", "testes",
                                    "arquitetura", "componentes"]},
                {"nome": "Sistemas Distribuídos",
                 "palavras_chave": ["nuvem", "escalabilidade", "tolerância a falhas",
                                    "contêineres", "borda", "latência"]},
                {"nome": "Computação Aplicada à Educação",
                 "palavras_chave": ["educação", "ensino", "aprendizagem", "avaliação automática",
                                    "feedback", "ambiente virtual", "estudantes"]},
            ],
        }

    # --- HOTSPOT: validação ------------------------------------------------
    def criar_validador(self):
        return ValidadorRigoroso(min_palavras=50, max_palavras=300,
                                 min_palavras_chave=3, max_palavras_chave=5, max_autores=8)

    # --- HOTSPOT: alocação de revisores -----------------------------------
    def criar_estrategia_alocacao(self):
        return AlocacaoPorAfinidade(revisores_por_trabalho=3, evitar_mesma_instituicao=True)

    # --- HOTSPOT: formulário de avaliação ---------------------------------
    def criar_formulario_avaliacao(self):
        return FormularioPonderado(comentario_minimo=30)  # critérios padrão: 30/20/30/20 %

    # --- HOTSPOT: política de decisão -------------------------------------
    def criar_politica_decisao(self):
        return DecisaoPorMediaPonderada(limiar_oral=3.5, limiar_poster=3.0, limiar_divergencia=1.0)

    # --- HOTSPOT: geração da programação ----------------------------------
    def criar_gerador_programacao(self):
        return ProgramacaoPorTrilhas(salas=("Auditório A", "Sala 101", "Sala 102"),
                                     artigos_por_sessao=3, duracao_min=20, inicio="09:00")

    # --- HOTSPOT: canal de notificação ------------------------------------
    def criar_canal_notificacao(self):
        return NotificacaoEmail(remetente="comissao@cbca2026.example")

    # --- GANCHO sobrescrito: usa agentes de IA ----------------------------
    def criar_assistente(self):
        return AssistenteAgentes(self.servicos.agentes)

    # --- GANCHO sobrescrito: dados de demonstração ------------------------
    def dados_de_exemplo(self) -> dict:
        return {"revisores": REVISORES, "submissoes": SUBMISSOES}

    # ocultar_autores_na_revisao() não é sobrescrito: vale o padrão (revisão cega).
