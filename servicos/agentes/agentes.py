"""
Agentes de IA do SciEvent, inspirados no MetaGPT (Hong et al., ICLR 2024).

Ideias aproveitadas do artigo:
  - cada agente tem PERFIL (nome, papel, objetivo, restrições), como os
    papéis Product Manager, Arquiteto etc. do MetaGPT;
  - os agentes não conversam livremente: trocam MENSAGENS ESTRUTURADAS com
    campos fixos (o "SOP" do processo de revisão);
  - as mensagens passam por um POOL COMPARTILHADO com publish-subscribe:
    cada agente assina só os tipos de mensagem que interessam ao seu papel.

Modelo de linguagem: se as variáveis SCIEVENT_LLM_URL e SCIEVENT_LLM_MODELO
estiverem definidas, os agentes usam qualquer API compatível com a da OpenAI
(OpenAI, Ollama, llama.cpp server, LM Studio...). Sem elas, cada agente usa
sua regra heurística local, e o sistema funciona 100% offline.
"""
from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from statistics import mean, pstdev
from typing import Optional

import requests

from scievent.chassi import BancoSQLite, agora, de_json, para_json

log = logging.getLogger("agentes")


# ---------------------------------------------------------------------------
# Modelos de linguagem (componente com interface)
# ---------------------------------------------------------------------------

class IModeloLinguagem(ABC):
    nome: str = ""

    @abstractmethod
    def responder_json(self, sistema: str, usuario: str) -> Optional[dict]:
        """Devolve um dicionário, ou None para o agente usar a heurística local."""


class ModeloHeuristico(IModeloLinguagem):
    nome = "heurístico (offline)"

    def responder_json(self, sistema, usuario):
        return None


class ModeloOpenAICompativel(IModeloLinguagem):
    def __init__(self, url_base: str, modelo: str, chave: str = ""):
        self.url = url_base.rstrip("/")
        self.modelo = modelo
        self.chave = chave
        self.nome = f"{modelo} ({self.url})"

    def responder_json(self, sistema, usuario):
        cabecalhos = {"Authorization": f"Bearer {self.chave}"} if self.chave else {}
        resposta = requests.post(
            f"{self.url}/chat/completions", headers=cabecalhos, timeout=110,
            json={"model": self.modelo, "temperature": 0.2,
                  "messages": [{"role": "system", "content": sistema},
                               {"role": "user", "content": usuario}]})
        resposta.raise_for_status()
        return extrair_json(resposta.json()["choices"][0]["message"]["content"])


def extrair_json(texto: str) -> Optional[dict]:
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio < 0 or fim <= inicio:
        return None
    try:
        return json.loads(texto[inicio:fim + 1])
    except ValueError:
        return None


def modelo_do_ambiente() -> IModeloLinguagem:
    url, modelo = os.environ.get("SCIEVENT_LLM_URL"), os.environ.get("SCIEVENT_LLM_MODELO")
    if url and modelo:
        return ModeloOpenAICompativel(url, modelo, os.environ.get("SCIEVENT_LLM_CHAVE", ""))
    return ModeloHeuristico()


# ---------------------------------------------------------------------------
# Agentes
# ---------------------------------------------------------------------------

class Agente(ABC):
    """Agente com perfil fixo que reage a tipos de mensagem do pool."""

    nome = ""
    papel = ""
    objetivo = ""
    restricoes = ""
    interesses: set[str] = set()   # tipos de mensagem que o agente assina
    produz = ""                    # tipo de mensagem que o agente publica
    campos_saida: list[str] = []   # schema da mensagem produzida

    def __init__(self, modelo: IModeloLinguagem):
        self.modelo = modelo

    def perfil(self) -> dict:
        return {"nome": self.nome, "papel": self.papel, "objetivo": self.objetivo,
                "restricoes": self.restricoes, "assina": sorted(self.interesses),
                "publica": self.produz, "campos": self.campos_saida}

    def agir(self, conteudo: dict) -> dict:
        resposta = None
        try:
            resposta = self.modelo.responder_json(self._instrucoes(), self.montar_pedido(conteudo))
        except (requests.RequestException, KeyError, ValueError) as erro:
            log.warning("%s: modelo indisponível (%s); usando heurística", self.nome, erro)
        if resposta and all(campo in resposta for campo in self.campos_saida):
            resposta["gerado_por"] = self.modelo.nome
        else:
            resposta = self.heuristica(conteudo)
            resposta["gerado_por"] = "heurística local"
        return resposta

    def _instrucoes(self) -> str:
        return (f"Você é {self.nome}, {self.papel} na comissão de um evento científico.\n"
                f"Objetivo: {self.objetivo}\nRestrições: {self.restricoes}\n"
                f"Responda SOMENTE com um objeto JSON contendo as chaves: {', '.join(self.campos_saida)}.")

    @abstractmethod
    def montar_pedido(self, conteudo: dict) -> str: ...

    @abstractmethod
    def heuristica(self, conteudo: dict) -> dict: ...


class AgenteTriagem(Agente):
    nome = "Ana"
    papel = "Agente de Triagem"
    objetivo = "Verificar a aderência da submissão às trilhas do evento e apontar problemas antes da revisão."
    restricoes = "Não julgar o mérito científico; apenas aderência, completude e clareza do resumo."
    interesses = {"SubmissaoRecebida"}
    produz = "TriagemConcluida"
    campos_saida = ["trilha_sugerida", "aderencia", "palavras_chave_sugeridas", "alertas", "resumo"]

    def montar_pedido(self, conteudo):
        return ("Trilhas do evento:\n" + json.dumps(conteudo["evento"]["trilhas"], ensure_ascii=False)
                + "\n\nSubmissão:\n" + json.dumps(conteudo["submissao"], ensure_ascii=False)
                + "\n\n'aderencia' é um número de 0 a 1; 'alertas' é uma lista de frases curtas.")

    def heuristica(self, conteudo):
        sub, trilhas = conteudo["submissao"], conteudo["evento"].get("trilhas", [])
        texto = " ".join([sub.get("titulo", ""), sub.get("resumo", ""), " ".join(sub.get("palavras_chave", []))]).lower()
        pontos = {t["nome"]: sum(1 for kw in t.get("palavras_chave", []) if kw.lower() in texto) for t in trilhas}
        melhor = max(pontos, key=pontos.get) if pontos else sub.get("trilha", "")
        aderencia = round(min(1.0, pontos.get(melhor, 0) / 3), 2)
        kws_sub = {k.lower() for k in sub.get("palavras_chave", [])}
        trilha = next((t for t in trilhas if t["nome"] == melhor), {"palavras_chave": []})
        sugeridas = [k for k in trilha["palavras_chave"] if k.lower() in texto and k.lower() not in kws_sub][:3]

        alertas = []
        n_palavras = len(re.findall(r"\w+", sub.get("resumo", "")))
        if n_palavras < 60:
            alertas.append(f"Resumo curto ({n_palavras} palavras): pode faltar método ou resultado.")
        if not re.search(r"resultad|avalia|experiment|mostr|demonstr|indic", sub.get("resumo", "").lower()):
            alertas.append("O resumo não menciona resultados nem avaliação.")
        if sub.get("trilha") and melhor != sub["trilha"] and pontos.get(melhor, 0) > pontos.get(sub["trilha"], 0):
            alertas.append(f"Trilha informada '{sub['trilha']}' difere da sugerida '{melhor}'.")
        if aderencia == 0:
            alertas.append("Baixa aderência às trilhas do evento.")
        resumo = (f"Aderente à trilha '{melhor}' ({aderencia:.0%})"
                  + (f", com {len(alertas)} alerta(s)." if alertas else ", sem alertas."))
        return {"trilha_sugerida": melhor, "aderencia": aderencia,
                "palavras_chave_sugeridas": sugeridas, "alertas": alertas, "resumo": resumo}


class AgenteMetaRevisor(Agente):
    nome = "Bruno"
    papel = "Agente Meta-revisor"
    objetivo = "Consolidar as revisões de um trabalho num parecer único, coerente com a decisão da comissão."
    restricoes = "Usar apenas o que os revisores escreveram; não inventar críticas; ser cordial e objetivo."
    interesses = {"RevisoesConcluidas"}
    produz = "MetaRevisaoConcluida"
    campos_saida = ["texto", "pontos_fortes", "pontos_fracos", "divergencia"]

    def montar_pedido(self, conteudo):
        return ("Decisão da comissão:\n" + json.dumps(conteudo["decisao"], ensure_ascii=False)
                + "\n\nRevisões:\n" + json.dumps(conteudo["revisoes"], ensure_ascii=False)
                + "\n\n'texto' é o parecer em português (até 120 palavras); 'pontos_fortes' e "
                  "'pontos_fracos' são listas; 'divergencia' é true ou false.")

    def heuristica(self, conteudo):
        revisoes, decisao = conteudo["revisoes"], conteudo["decisao"]
        notas = [float(r["nota"]) for r in revisoes]
        desvio = pstdev(notas) if len(notas) > 1 else 0.0
        por_criterio: dict[str, list[float]] = {}
        for r in revisoes:
            for chave, valor in (r.get("respostas") or {}).items():
                por_criterio.setdefault(chave, []).append(float(valor))
        medias = {criterio: mean(valores) for criterio, valores in por_criterio.items()}
        variam = len(medias) > 1 and max(medias.values()) > min(medias.values())
        fortes = [max(medias, key=medias.get)] if variam else []
        fracos = [min(medias, key=medias.get)] if variam else []

        frases = []
        for r in revisoes:
            primeira = re.split(r"(?<=[.!?])\s", (r.get("comentario") or "").strip())[0]
            if primeira and primeira not in frases:
                frases.append(primeira)

        resultado = ("aceito" + (f" ({'pôster' if decisao.get('modalidade') == 'poster' else 'apresentação oral'})"
                                 if decisao.get("modalidade") else "")
                     if decisao["status"] == "aceito" else "não aceito")
        texto = (f"O trabalho recebeu {len(notas)} avaliação(ões), com nota média {mean(notas):.2f}. ")
        if fortes:
            texto += f"Ponto mais forte: {fortes[0]} ({medias[fortes[0]]:.1f}); mais fraco: {fracos[0]} ({medias[fracos[0]]:.1f}). "
        if frases:
            texto += "Síntese dos pareceres: " + " ".join(f"({i}) {f}" for i, f in enumerate(frases[:2], 1)) + " "
        divergencia = desvio > 1.0
        if divergencia:
            texto += f"Houve divergência entre os revisores (desvio {desvio:.2f}). "
        texto += f"Recomendação consolidada: {resultado}."
        return {"texto": texto, "pontos_fortes": fortes, "pontos_fracos": fracos, "divergencia": divergencia}


# ---------------------------------------------------------------------------
# Pool de mensagens com publish-subscribe
# ---------------------------------------------------------------------------

ESQUEMA_POOL = """
CREATE TABLE IF NOT EXISTS mensagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    origem TEXT NOT NULL,
    causa_id INTEGER,
    conteudo TEXT NOT NULL,
    criado_em TEXT NOT NULL
);
"""


class PoolDeMensagens:
    """Ambiente compartilhado: quem publica não conhece quem consome."""

    def __init__(self, banco: BancoSQLite):
        self.banco = banco
        self._assinantes: list[Agente] = []

    def assinar(self, agente: Agente) -> None:
        self._assinantes.append(agente)

    @property
    def agentes(self) -> list[Agente]:
        return list(self._assinantes)

    def publicar(self, evento_id: int, tipo: str, origem: str, conteudo: dict,
                 causa_id: Optional[int] = None) -> list[dict]:
        """Grava a mensagem, entrega aos assinantes e devolve ela + as que ela gerou."""
        novo_id = self.banco.executar(
            "INSERT INTO mensagens (evento_id, tipo, origem, causa_id, conteudo, criado_em) VALUES (?,?,?,?,?,?)",
            (evento_id, tipo, origem, causa_id, para_json(conteudo), agora()))
        mensagem = {"id": novo_id, "evento_id": evento_id, "tipo": tipo, "origem": origem,
                    "causa_id": causa_id, "conteudo": conteudo}
        geradas = [mensagem]
        for agente in self._assinantes:
            if tipo in agente.interesses:
                saida = agente.agir(conteudo)
                geradas += self.publicar(evento_id, agente.produz, f"{agente.nome} ({agente.papel})",
                                         saida, causa_id=novo_id)
        return geradas

    def listar(self, evento_id: int, limite: int = 200) -> list[dict]:
        linhas = self.banco.consultar(
            "SELECT * FROM mensagens WHERE evento_id = ? ORDER BY id DESC LIMIT ?", (evento_id, limite))
        for linha in linhas:
            linha["conteudo"] = de_json(linha["conteudo"], {})
        return linhas
