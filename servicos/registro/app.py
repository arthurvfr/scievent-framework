"""
Microsserviço REGISTRO (Service Registry) — porta 5010.

Faz o papel do Eureka na figura de referência da disciplina: cada
microsserviço se registra aqui ao subir e reenvia o registro a cada 5 s
(heartbeat). O gateway consulta este serviço para descobrir o endereço dos
demais e para montar a tela "Microsserviços em execução".

Endpoints:
    POST /servicos            registra ou renova um serviço (heartbeat)
    GET  /servicos            lista os serviços com status ativo/inativo
    GET  /servicos/<nome>     dados de um serviço
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from flask import jsonify  # noqa: E402

from scievent import config  # noqa: E402
from scievent.chassi import ErroNegocio, agora, corpo_json, criar_microsservico, iniciar  # noqa: E402

app = criar_microsservico("registro", "Service Registry: descoberta e saúde dos microsserviços")

# Armazenamento em memória: o registro é reconstruído pelos heartbeats.
_servicos: dict[str, dict] = {}


def _com_status(s: dict) -> dict:
    idade = time.time() - s["ultimo_heartbeat_ts"]
    return {**{k: v for k, v in s.items() if k != "ultimo_heartbeat_ts"},
            "ativo": idade <= config.TEMPO_EXPIRACAO,
            "segundos_desde_heartbeat": round(idade, 1)}


@app.post("/servicos")
def registrar():
    dados = corpo_json()
    for campo in ("nome", "url", "porta"):
        if campo not in dados:
            raise ErroNegocio(f"Campo obrigatório ausente: {campo}")
    anterior = _servicos.get(dados["nome"], {})
    _servicos[dados["nome"]] = {
        "nome": dados["nome"], "url": dados["url"], "porta": int(dados["porta"]),
        "descricao": dados.get("descricao", ""), "pid": dados.get("pid"),
        "registrado_em": anterior.get("registrado_em", agora()),
        "ultimo_heartbeat": agora(), "ultimo_heartbeat_ts": time.time(),
    }
    return jsonify(_com_status(_servicos[dados["nome"]])), 201


@app.get("/servicos")
def listar():
    proprio = {"nome": "registro", "url": f"http://{config.HOST}:{config.porta('registro')}",
               "porta": config.porta("registro"), "descricao": app.config["SCIEVENT_DESCRICAO"],
               "pid": os.getpid(), "registrado_em": _inicio, "ultimo_heartbeat": agora(),
               "ativo": True, "segundos_desde_heartbeat": 0.0}
    outros = [_com_status(s) for s in _servicos.values()]
    return jsonify(sorted([proprio, *outros], key=lambda s: s["porta"]))


@app.get("/servicos/<nome>")
def obter(nome):
    if nome not in _servicos:
        raise ErroNegocio(f"Serviço '{nome}' não registrado.", 404)
    return jsonify(_com_status(_servicos[nome]))


_inicio = agora()

if __name__ == "__main__":
    iniciar(app, registrar=False)
