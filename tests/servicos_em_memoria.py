"""
Dublê de teste: imita os microsserviços em memória, com a mesma interface
dos clientes de scievent.clientes. Permite testar os template methods do
framework sem subir nenhum processo.
"""
from __future__ import annotations

import itertools


class _Base:
    def __init__(self):
        self._ids = itertools.count(1)


class Eventos(_Base):
    def __init__(self):
        super().__init__()
        self.dados = {}

    def criar(self, dados):
        novo = {**dados, "id": next(self._ids)}
        self.dados[novo["id"]] = novo
        return novo

    def buscar_por_aplicacao(self, aplicacao):
        return [e for e in self.dados.values() if e["aplicacao"] == aplicacao]


class Submissoes(_Base):
    def __init__(self):
        super().__init__()
        self.dados = {}

    def criar(self, dados):
        novo = {**dados, "id": next(self._ids), "status": "submetida",
                "decisao": None, "triagem": None, "parecer": None}
        self.dados[novo["id"]] = novo
        return dict(novo)

    def listar(self, evento_id, status=None):
        return [dict(s) for s in self.dados.values()
                if s["evento_id"] == evento_id and (status is None or s["status"] == status)]

    def atualizar(self, submissao_id, **campos):
        self.dados[submissao_id].update(campos)
        return dict(self.dados[submissao_id])


class Revisoes(_Base):
    def __init__(self):
        super().__init__()
        self.revisores, self.alocacoes, self.revisoes = {}, {}, {}

    def criar_revisor(self, evento_id, dados):
        novo = {**dados, "id": next(self._ids), "evento_id": evento_id}
        self.revisores[novo["id"]] = novo
        return novo

    def listar_revisores(self, evento_id):
        return [r for r in self.revisores.values() if r["evento_id"] == evento_id]

    def criar_alocacoes(self, evento_id, pares):
        criadas = []
        for p in pares:
            nova = {**p, "id": next(self._ids), "evento_id": evento_id, "status": "pendente",
                    "revisor_nome": self.revisores[p["revisor_id"]]["nome"]}
            self.alocacoes[nova["id"]] = nova
            criadas.append(nova)
        return criadas

    def listar_alocacoes(self, **f):
        return [a for a in self.alocacoes.values()
                if all(a.get(k) == v for k, v in f.items() if v is not None)]

    def registrar_revisao(self, alocacao_id, respostas, comentario, nota):
        a = self.alocacoes[alocacao_id]
        a["status"] = "concluida"
        nova = {"id": next(self._ids), "alocacao_id": alocacao_id, "submissao_id": a["submissao_id"],
                "evento_id": a["evento_id"], "revisor_id": a["revisor_id"], "revisor_nome": a["revisor_nome"],
                "respostas": respostas, "comentario": comentario, "nota": nota}
        self.revisoes[nova["id"]] = nova
        return nova

    def listar_revisoes(self, **f):
        return [r for r in self.revisoes.values()
                if all(r.get(k) == v for k, v in f.items() if v is not None)]


class Programacao:
    def __init__(self):
        self.dados = {}

    def salvar(self, evento_id, programa):
        self.dados[evento_id] = {**programa, "evento_id": evento_id, "publicado_em": "agora"}
        return self.dados[evento_id]

    def obter(self, evento_id):
        return self.dados.get(evento_id)


class Notificacoes:
    def __init__(self):
        self.enviadas = []

    def enviar(self, dados):
        self.enviadas.append(dados)
        return dados

    def listar(self, evento_id):
        return [n for n in self.enviadas if n["evento_id"] == evento_id]


class Agentes:
    def triagem(self, evento, submissao):
        return {"trilha_sugerida": submissao.get("trilha"), "aderencia": 1.0,
                "palavras_chave_sugeridas": [], "alertas": [], "resumo": "ok"}

    def meta_revisao(self, evento, submissao, revisoes, decisao):
        return {"texto": f"Parecer consolidado de {len(revisoes)} revisões."}


class ServicosEmMemoria:
    def __init__(self):
        self.eventos = Eventos()
        self.submissoes = Submissoes()
        self.revisoes = Revisoes()
        self.programacao = Programacao()
        self.notificacoes = Notificacoes()
        self.agentes = Agentes()
