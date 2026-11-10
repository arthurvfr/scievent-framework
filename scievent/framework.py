"""
Núcleo do SciEvent: a classe de controle do framework.

Padrão de projeto: TEMPLATE METHOD.
  - Os métodos marcados como TEMPLATE METHOD definem o fluxo fixo de qualquer
    evento científico (frozen spots). As aplicações NÃO os sobrescrevem.
  - Os métodos marcados como HOTSPOT são os pontos de adaptação. Cada
    aplicação implementa os hotspots abstratos e, se quiser, os ganchos
    (hotspots com implementação padrão).

Fluxo fixo de um evento (cada etapa usa um ou mais microsserviços):

    inicializar()          -> eventos
    submeter_trabalho()    -> submissoes, agentes*, notificacoes
    alocar_revisores()     -> submissoes, revisoes, notificacoes
    registrar_revisao()    -> revisoes
    consolidar_decisoes()  -> submissoes, revisoes, agentes*, notificacoes
    gerar_programacao()    -> submissoes, programacao, notificacoes
                                               (* somente se houver assistente)
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import Counter
from typing import Optional, final

from scievent.clientes import ErroServico, ServicosSciEvent
from scievent.componentes.assistente import SemAssistente
from scievent.interfaces import (
    IAssistente, ICanalNotificacao, IEstrategiaAlocacao, IFormularioAvaliacao,
    IGeradorProgramacao, IPoliticaDecisao, IValidadorSubmissao,
)
from scievent.modelos import ResultadoRevisao, ResultadoSubmissao

log = logging.getLogger("scievent.framework")


class FrameworkEventoCientifico(ABC):
    """
    Classe abstrata do framework. Para criar uma aplicação (um sistema para
    um evento específico), herde desta classe, defina ID_APLICACAO e
    implemente os hotspots.
    """

    #: Identificador curto da aplicação (usado na URL /a/<ID_APLICACAO>/).
    ID_APLICACAO: str = ""

    #: Quantas vezes o núcleo tenta gerar uma programação sem conflitos.
    MAX_TENTATIVAS_PROGRAMACAO = 3

    def __init__(self, servicos: Optional[ServicosSciEvent] = None):
        if not self.ID_APLICACAO:
            raise TypeError(f"{type(self).__name__} precisa definir ID_APLICACAO.")
        self.servicos = servicos or ServicosSciEvent()
        # Cada hotspot é resolvido uma única vez (Factory Methods).
        self.validador: IValidadorSubmissao = self.criar_validador()
        self.alocacao: IEstrategiaAlocacao = self.criar_estrategia_alocacao()
        self.formulario: IFormularioAvaliacao = self.criar_formulario_avaliacao()
        self.politica_decisao: IPoliticaDecisao = self.criar_politica_decisao()
        self.gerador_programacao: IGeradorProgramacao = self.criar_gerador_programacao()
        self.canal_notificacao: ICanalNotificacao = self.criar_canal_notificacao()
        self.assistente: IAssistente = self.criar_assistente()
        self._evento: Optional[dict] = None

    # =====================================================================
    # HOTSPOTS ABSTRATOS: toda aplicação é obrigada a implementar
    # =====================================================================

    @abstractmethod
    def definir_evento(self) -> dict:
        """
        HOTSPOT: dados do evento.
        Deve devolver {"nome", "sigla", "descricao", "local", "data_inicio",
        "data_fim", "trilhas": [{"nome", "palavras_chave": [..]}]}.
        """

    @abstractmethod
    def criar_validador(self) -> IValidadorSubmissao:
        """HOTSPOT: regras que uma submissão precisa cumprir."""

    @abstractmethod
    def criar_estrategia_alocacao(self) -> IEstrategiaAlocacao:
        """HOTSPOT: como os trabalhos são distribuídos entre os revisores."""

    @abstractmethod
    def criar_formulario_avaliacao(self) -> IFormularioAvaliacao:
        """HOTSPOT: o que o revisor preenche e como isso vira uma nota."""

    @abstractmethod
    def criar_politica_decisao(self) -> IPoliticaDecisao:
        """HOTSPOT: como as notas viram aceite (oral/pôster) ou rejeição."""

    @abstractmethod
    def criar_gerador_programacao(self) -> IGeradorProgramacao:
        """HOTSPOT: como a grade do evento é montada."""

    @abstractmethod
    def criar_canal_notificacao(self) -> ICanalNotificacao:
        """HOTSPOT: por onde e com que texto os participantes são avisados."""

    # =====================================================================
    # GANCHOS (hotspots com implementação padrão; sobrescrever é opcional)
    # =====================================================================

    def criar_assistente(self) -> IAssistente:
        """GANCHO: assistente de IA. Padrão: nenhum (SemAssistente)."""
        return SemAssistente()

    def ocultar_autores_na_revisao(self) -> bool:
        """GANCHO: revisão cega? Padrão: sim (o revisor não vê os autores)."""
        return True

    def dados_de_exemplo(self) -> dict:
        """GANCHO: dados de demonstração {"revisores": [..], "submissoes": [..]}."""
        return {"revisores": [], "submissoes": []}

    # =====================================================================
    # TEMPLATE METHODS (frozen spots): fluxo fixo, não sobrescrever
    # =====================================================================

    @final
    def inicializar(self) -> dict:
        """
        TEMPLATE METHOD 1: garante que o evento da aplicação existe.
        Na primeira execução cria o evento no microsserviço 'eventos',
        gravando também quais componentes foram plugados em cada hotspot.
        """
        if self._evento is None:
            existentes = self.servicos.eventos.buscar_por_aplicacao(self.ID_APLICACAO)
            if existentes:
                self._evento = existentes[0]
            else:
                dados = self.definir_evento()                       # hotspot
                dados["aplicacao"] = self.ID_APLICACAO
                dados["componentes"] = self.descrever_componentes()
                self._evento = self.servicos.eventos.criar(dados)
        return self._evento

    @final
    def submeter_trabalho(self, dados: dict) -> ResultadoSubmissao:
        """
        TEMPLATE METHOD 2: recebe uma submissão.
          1. normaliza os dados               (fixo)
          2. valida                           (hotspot: validador)
          3. grava no microsserviço           (fixo)
          4. triagem por IA                   (gancho: assistente)
          5. avisa o autor                    (hotspot: canal de notificação)
        """
        evento = self.inicializar()
        dados = self._normalizar_submissao(dados)
        erros = self.validador.validar(dados, evento)
        if erros:
            return ResultadoSubmissao(aceita=False, erros=erros)

        sub = self.servicos.submissoes.criar({**dados, "evento_id": evento["id"]})
        triagem = self.assistente.triar(sub, evento)
        if triagem:
            sub = self.servicos.submissoes.atualizar(sub["id"], triagem=triagem)
        self._notificar("submissao_recebida", sub["autores"][0]["email"],
                        {"titulo": sub["titulo"], "id": sub["id"]})
        return ResultadoSubmissao(aceita=True, submissao=sub)

    @final
    def alocar_revisores(self) -> list[dict]:
        """
        TEMPLATE METHOD 3: distribui os trabalhos ainda sem revisor.
          1. busca trabalhos 'submetida' e revisores        (fixo)
          2. calcula a carga atual de cada revisor          (fixo)
          3. escolhe os pares trabalho-revisor               (hotspot: alocação)
          4. grava as alocações e muda o status              (fixo)
          5. convida cada revisor                            (hotspot: notificação)
        """
        evento = self.inicializar()
        pendentes = self.servicos.submissoes.listar(evento["id"], status="submetida")
        revisores = self.servicos.revisoes.listar_revisores(evento["id"])
        if not pendentes or not revisores:
            return []

        carga = Counter(a["revisor_id"] for a in self.servicos.revisoes.listar_alocacoes(evento_id=evento["id"]))
        pares = self.alocacao.alocar(pendentes, revisores, dict(carga))
        if not pares:
            return []
        alocacoes = self.servicos.revisoes.criar_alocacoes(evento["id"], pares)

        for sub_id in {p["submissao_id"] for p in pares}:
            self.servicos.submissoes.atualizar(sub_id, status="em_revisao")
        por_revisor = Counter(p["revisor_id"] for p in pares)
        for r in revisores:
            if r["id"] in por_revisor:
                self._notificar("convite_revisao", r["email"],
                                {"nome": r["nome"], "quantidade": por_revisor[r["id"]]})
        return alocacoes

    @final
    def registrar_revisao(self, alocacao_id: int, respostas: dict, comentario: str) -> ResultadoRevisao:
        """
        TEMPLATE METHOD 4: grava a avaliação de um revisor.
          1. valida as respostas             (hotspot: formulário)
          2. calcula a nota                  (hotspot: formulário)
          3. grava no microsserviço          (fixo)
        """
        erros = self.formulario.validar(respostas, comentario)
        if erros:
            return ResultadoRevisao(registrada=False, erros=erros)
        nota = self.formulario.calcular_nota(respostas)
        revisao = self.servicos.revisoes.registrar_revisao(alocacao_id, respostas, comentario, nota)
        return ResultadoRevisao(registrada=True, revisao=revisao)

    @final
    def consolidar_decisoes(self) -> list[dict]:
        """
        TEMPLATE METHOD 5: decide os trabalhos com todas as revisões entregues.
          1. junta as notas de cada trabalho em revisão   (fixo)
          2. decide                                        (hotspot: política de decisão)
          3. parecer consolidado por IA                    (gancho: assistente)
          4. grava a decisão                               (fixo)
          5. avisa o autor                                 (hotspot: notificação)
        """
        evento = self.inicializar()
        rotulos = {c.chave: c.rotulo for c in self.formulario.criterios()}
        decididas = []
        for sub in self.servicos.submissoes.listar(evento["id"], status="em_revisao"):
            alocacoes = self.servicos.revisoes.listar_alocacoes(submissao_id=sub["id"])
            revisoes = self.servicos.revisoes.listar_revisoes(submissao_id=sub["id"])
            if not revisoes or len(revisoes) < len(alocacoes):
                continue  # ainda há revisão pendente

            decisao = self.politica_decisao.decidir(sub, [r["nota"] for r in revisoes])
            # o assistente recebe as respostas com o nome legível de cada critério
            rotuladas = [{**r, "respostas": {rotulos.get(k, k): v for k, v in r["respostas"].items()}}
                         for r in revisoes]
            parecer = self.assistente.meta_revisao(sub, rotuladas, decisao, evento)
            atualizada = self.servicos.submissoes.atualizar(
                sub["id"], status=decisao.status, decisao=decisao.como_dict(), parecer=parecer)
            self._notificar("decisao", sub["autores"][0]["email"],
                            {"titulo": sub["titulo"], **decisao.como_dict()})
            decididas.append(atualizada)
        return decididas

    @final
    def gerar_programacao(self) -> dict:
        """
        TEMPLATE METHOD 6: monta a programação com os trabalhos aceitos.
        Gera e verifica em laço (até MAX_TENTATIVAS_PROGRAMACAO): se o
        componente encontrar conflitos, pede uma nova tentativa e guarda a
        melhor versão. Inspirado no feedback executável do MetaGPT.
          1. busca os aceitos                       (fixo)
          2. gera a grade                           (hotspot: gerador)
          3. verifica conflitos                     (hotspot: gerador)
          4. repete ou aceita                       (fixo)
          5. publica e avisa                        (fixo + hotspot: notificação)
        """
        evento = self.inicializar()
        aceitos = self.servicos.submissoes.listar(evento["id"], status="aceito")
        melhor, conflitos_melhor, historico = None, None, []
        for tentativa in range(1, self.MAX_TENTATIVAS_PROGRAMACAO + 1):
            programa = self.gerador_programacao.gerar(aceitos, evento, tentativa)
            conflitos = self.gerador_programacao.verificar_conflitos(programa)
            historico.append({"tentativa": tentativa, "conflitos": conflitos})
            if melhor is None or len(conflitos) < len(conflitos_melhor):
                melhor, conflitos_melhor = programa, conflitos
            if not conflitos:
                break

        resultado = {**melhor.como_dict(), "tentativas": historico, "conflitos": conflitos_melhor,
                     "componente": self.gerador_programacao.nome}
        salvo = self.servicos.programacao.salvar(evento["id"], resultado)
        self._notificar("programacao_publicada", "todos os participantes",
                        {"sessoes": len(melhor.sessoes)})
        return salvo

    # =====================================================================
    # Métodos auxiliares fixos
    # =====================================================================

    @final
    def descrever_componentes(self) -> list[dict]:
        """Lista os componentes plugados em cada hotspot (exibida na interface)."""
        hotspots = [
            ("Validação de submissão", self.validador),
            ("Alocação de revisores", self.alocacao),
            ("Formulário de avaliação", self.formulario),
            ("Política de decisão", self.politica_decisao),
            ("Geração de programação", self.gerador_programacao),
            ("Canal de notificação", self.canal_notificacao),
            ("Assistente de IA", self.assistente),
        ]
        return [{"hotspot": h, "componente": c.nome, "descricao": c.descricao()} for h, c in hotspots]

    def _normalizar_submissao(self, dados: dict) -> dict:
        kws = dados.get("palavras_chave") or []
        if isinstance(kws, str):
            kws = [k for k in (p.strip() for p in kws.replace(";", ",").split(",")) if k]
        autores = [{k: (a.get(k) or "").strip() for k in ("nome", "email", "instituicao")}
                   for a in (dados.get("autores") or [])]
        return {
            "titulo": (dados.get("titulo") or "").strip(),
            "resumo": (dados.get("resumo") or "").strip(),
            "palavras_chave": kws,
            "trilha": (dados.get("trilha") or "").strip(),
            "autores": [a for a in autores if a["nome"] or a["email"]],
        }

    def _notificar(self, tipo: str, destinatario: str, contexto: dict) -> None:
        """Formata pelo canal escolhido e envia pelo microsserviço de notificações."""
        evento = self.inicializar()
        mensagem = self.canal_notificacao.formatar(tipo, {**contexto, "evento": evento["sigla"]})
        try:
            self.servicos.notificacoes.enviar({
                "evento_id": evento["id"], "canal": self.canal_notificacao.canal,
                "tipo": tipo, "destinatario": destinatario,
                "assunto": mensagem.assunto, "corpo": mensagem.corpo,
            })
        except ErroServico as erro:
            # Notificar não é crítico: o fluxo principal segue mesmo se falhar.
            log.warning("Notificação não enviada: %s", erro)
