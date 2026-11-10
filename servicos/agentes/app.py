"""
Microsserviço AGENTES (opcional) — porta 5006 — banco: data/agentes.db (SQLite).

Hospeda os agentes de IA e o pool de mensagens (ver agentes.py). O framework
fala com este serviço pelo componente AssistenteAgentes; aplicações que usam
SemAssistente nunca o chamam.

Endpoints:
    POST /triagem         publica 'SubmissaoRecebida' e devolve 'TriagemConcluida'
    POST /meta-revisao    publica 'RevisoesConcluidas' e devolve 'MetaRevisaoConcluida'
    GET  /pool?evento_id  mensagens trocadas no pool (mais recentes primeiro)
    GET  /papeis          perfil de cada agente (papel, objetivo, assinaturas)
    GET  /modelo          modelo de linguagem em uso
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import jsonify, request  # noqa: E402

from agentes import (ESQUEMA_POOL, AgenteMetaRevisor, AgenteTriagem,  # noqa: E402
                     PoolDeMensagens, modelo_do_ambiente)
from scievent.chassi import BancoSQLite, ErroNegocio, corpo_json, criar_microsservico, iniciar  # noqa: E402

app = criar_microsservico("agentes", "Agentes de IA (triagem e meta-revisão) com pool de mensagens")

modelo = modelo_do_ambiente()
pool = PoolDeMensagens(BancoSQLite("agentes", ESQUEMA_POOL))
pool.assinar(AgenteTriagem(modelo))
pool.assinar(AgenteMetaRevisor(modelo))


def _resposta(mensagens: list[dict], tipo: str) -> dict:
    produzida = next((m for m in mensagens if m["tipo"] == tipo), None)
    if not produzida:
        raise ErroNegocio(f"Nenhum agente produziu '{tipo}'.", 500)
    return {**produzida["conteudo"], "mensagem_id": produzida["id"]}


@app.post("/triagem")
def triagem():
    dados = corpo_json()
    evento, sub = dados.get("evento"), dados.get("submissao")
    if not evento or not sub:
        raise ErroNegocio("Envie 'evento' e 'submissao'.")
    conteudo = {
        "evento": {"sigla": evento.get("sigla"), "trilhas": evento.get("trilhas", [])},
        "submissao": {k: sub.get(k) for k in ("id", "titulo", "resumo", "palavras_chave", "trilha")},
    }
    mensagens = pool.publicar(evento["id"], "SubmissaoRecebida", "Framework SciEvent", conteudo)
    return jsonify(_resposta(mensagens, "TriagemConcluida"))


@app.post("/meta-revisao")
def meta_revisao():
    dados = corpo_json()
    evento, sub = dados.get("evento"), dados.get("submissao")
    if not evento or not sub or not dados.get("revisoes"):
        raise ErroNegocio("Envie 'evento', 'submissao', 'revisoes' e 'decisao'.")
    conteudo = {
        "submissao": {"id": sub["id"], "titulo": sub["titulo"]},
        "decisao": dados.get("decisao", {}),
        "revisoes": [{k: r.get(k) for k in ("revisor_nome", "nota", "respostas", "comentario")}
                     for r in dados["revisoes"]],
    }
    mensagens = pool.publicar(evento["id"], "RevisoesConcluidas", "Framework SciEvent", conteudo)
    return jsonify(_resposta(mensagens, "MetaRevisaoConcluida"))


@app.get("/pool")
def listar_pool():
    evento_id = request.args.get("evento_id", type=int)
    if evento_id is None:
        raise ErroNegocio("Informe o parâmetro evento_id.")
    return jsonify(pool.listar(evento_id))


@app.get("/papeis")
def papeis():
    return jsonify([agente.perfil() for agente in pool.agentes])


@app.get("/modelo")
def info_modelo():
    return jsonify({"modelo": modelo.nome, "usa_llm": type(modelo).__name__ != "ModeloHeuristico"})


if __name__ == "__main__":
    iniciar(app)
