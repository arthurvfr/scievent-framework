"""
Testes do núcleo do framework: executam os template methods das duas
aplicações com os microsserviços substituídos por um dublê em memória.
"""
import pytest

from apps.congresso_nacional.aplicacao import CongressoNacional
from apps.jornada_ic.aplicacao import JornadaIniciacaoCientifica
from scievent import demo
from scievent.componentes import (AlocacaoRoundRobin, DecisaoPorNotaMinima, FormularioNotaUnica,
                                  NotificacaoMural, ProgramacaoSequencial, ValidadorSimples)
from scievent.framework import FrameworkEventoCientifico
from tests.servicos_em_memoria import ServicosEmMemoria


@pytest.mark.parametrize("classe", [CongressoNacional, JornadaIniciacaoCientifica])
def test_ciclo_completo_de_cada_aplicacao(classe):
    servicos = ServicosEmMemoria()
    app = classe(servicos)

    carga = demo.popular(app)
    assert carga["submissoes"] == len(app.dados_de_exemplo()["submissoes"])
    assert carga["recusadas"] == []

    assert app.alocar_revisores()
    assert demo.simular_revisoes(app) > 0
    decididas = app.consolidar_decisoes()
    assert len(decididas) == carga["submissoes"]
    assert any(d["status"] == "aceito" for d in decididas)

    programa = app.gerar_programacao()
    assert programa["sessoes"]
    assert 1 <= len(programa["tentativas"]) <= app.MAX_TENTATIVAS_PROGRAMACAO

    tipos = {n["tipo"] for n in servicos.notificacoes.enviadas}
    assert tipos == {"submissao_recebida", "convite_revisao", "decisao", "programacao_publicada"}
    assert {n["canal"] for n in servicos.notificacoes.enviadas} == {app.canal_notificacao.canal}


def test_congresso_usa_assistente_e_jornada_nao():
    s1, s2 = ServicosEmMemoria(), ServicosEmMemoria()
    congresso, jornada = CongressoNacional(s1), JornadaIniciacaoCientifica(s2)
    demo.popular(congresso)
    demo.popular(jornada)
    assert all(s["triagem"] for s in s1.submissoes.dados.values())
    assert not any(s["triagem"] for s in s2.submissoes.dados.values())


def test_submissao_invalida_nao_chega_ao_microsservico():
    servicos = ServicosEmMemoria()
    resultado = CongressoNacional(servicos).submeter_trabalho({"titulo": "curto", "resumo": "x", "autores": []})
    assert not resultado.aceita and resultado.erros
    assert servicos.submissoes.dados == {}


def test_nova_aplicacao_precisa_implementar_os_hotspots():
    class Incompleta(FrameworkEventoCientifico):
        ID_APLICACAO = "incompleta"

    with pytest.raises(TypeError):
        Incompleta(ServicosEmMemoria())


def test_nova_aplicacao_do_tutorial_funciona():
    """Executa o mesmo código do passo a passo 'Como criar uma nova aplicação' do README."""
    from statistics import mean

    from scievent.interfaces import IPoliticaDecisao
    from scievent.modelos import Decisao

    class DecisaoPorConsenso(IPoliticaDecisao):
        def __init__(self, nota_minima=7.0):
            self.nota_minima = nota_minima

        def descricao(self):
            return f"Aceita só se TODOS os revisores derem nota >= {self.nota_minima}"

        def decidir(self, submissao, notas):
            media = round(mean(notas), 2)
            if min(notas) >= self.nota_minima:
                return Decisao("aceito", "oral", media, "Consenso entre os revisores.")
            return Decisao("rejeitado", None, media, f"Ao menos uma nota abaixo de {self.nota_minima}.")

    class WorkshopIA(FrameworkEventoCientifico):
        ID_APLICACAO = "workshop"

        def definir_evento(self):
            return {"nome": "Workshop de Inteligência Artificial", "sigla": "WIA 2026",
                    "descricao": "Workshop de um dia.", "local": "Maceió - AL",
                    "data_inicio": "2026-12-15", "data_fim": "2026-12-15",
                    "trilhas": [{"nome": "IA", "palavras_chave": ["aprendizado", "agentes"]}]}

        def criar_validador(self):
            return ValidadorSimples(max_palavras=200)

        def criar_estrategia_alocacao(self):
            return AlocacaoRoundRobin(revisores_por_trabalho=2)

        def criar_formulario_avaliacao(self):
            return FormularioNotaUnica(minimo=0, maximo=10)

        def criar_politica_decisao(self):
            return DecisaoPorConsenso(nota_minima=7.0)

        def criar_gerador_programacao(self):
            return ProgramacaoSequencial(sala="Laboratório 1", inicio="09:00")

        def criar_canal_notificacao(self):
            return NotificacaoMural()

    servicos = ServicosEmMemoria()
    app = WorkshopIA(servicos)
    assert app.inicializar()["sigla"] == "WIA 2026"
    for email in ("r1@x.br", "r2@x.br"):
        servicos.revisoes.criar_revisor(app.inicializar()["id"], {"nome": email, "email": email})
    assert app.submeter_trabalho({"titulo": "T", "resumo": "Um resumo.",
                                  "autores": [{"nome": "A", "email": "a@x.br"}]}).aceita
    alocacoes = app.alocar_revisores()
    assert len(alocacoes) == 2
    app.registrar_revisao(alocacoes[0]["id"], {"nota": 9}, "")
    app.registrar_revisao(alocacoes[1]["id"], {"nota": 6}, "")
    assert app.consolidar_decisoes()[0]["status"] == "rejeitado"   # sem consenso
