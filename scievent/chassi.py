"""
Chassi de microsserviço (padrão Microservice Chassis).

O que é igual em todos os microsserviços fica aqui, escrito uma única vez:
  - criação do app Flask com CORS e respostas de erro em JSON;
  - rota GET /health (verificação de saúde) e GET / (lista de endpoints);
  - registro e heartbeat no Service Registry;
  - acesso a um banco SQLite exclusivo do serviço (database per service).
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterable

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from scievent import config


def agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def para_json(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False)


def de_json(texto: str | None, padrao: Any = None) -> Any:
    return json.loads(texto) if texto else padrao


class BancoSQLite:
    """Banco SQLite exclusivo de um microsserviço, criado em data/<servico>.db."""

    def __init__(self, servico: str, esquema: str):
        os.makedirs(config.PASTA_DADOS, exist_ok=True)
        self.caminho = os.path.join(config.PASTA_DADOS, f"{servico}.db")
        with self._conexao() as con:
            con.executescript(esquema)

    @contextmanager
    def _conexao(self):
        con = sqlite3.connect(self.caminho, timeout=10)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def consultar(self, sql: str, parametros: Iterable = ()) -> list[dict]:
        with self._conexao() as con:
            return [dict(linha) for linha in con.execute(sql, tuple(parametros)).fetchall()]

    def executar(self, sql: str, parametros: Iterable = ()) -> int:
        """Executa INSERT/UPDATE/DELETE e devolve o id da última linha inserida."""
        with self._conexao() as con:
            return con.execute(sql, tuple(parametros)).lastrowid


class ErroNegocio(Exception):
    """Erro previsto (dado inválido, recurso inexistente) devolvido como JSON."""

    def __init__(self, mensagem: str, status: int = 400):
        super().__init__(mensagem)
        self.status = status


def criar_microsservico(nome: str, descricao: str) -> Flask:
    """Cria o app Flask de um microsserviço com as rotas e tratadores comuns."""
    app = Flask(nome)
    app.config["JSON_AS_ASCII"] = False
    app.json.ensure_ascii = False
    app.config["SCIEVENT_NOME"] = nome
    app.config["SCIEVENT_DESCRICAO"] = descricao
    CORS(app)

    @app.get("/health")
    def saude():
        return jsonify({"servico": nome, "status": "ok", "hora": agora()})

    @app.get("/")
    def indice():
        rotas = sorted(
            {f"{metodo} {regra.rule}"
             for regra in app.url_map.iter_rules() if regra.endpoint != "static"
             for metodo in regra.methods - {"HEAD", "OPTIONS"}}
        )
        return jsonify({"servico": nome, "descricao": descricao,
                        "porta": config.porta(nome), "endpoints": rotas})

    @app.errorhandler(ErroNegocio)
    def erro_negocio(erro: ErroNegocio):
        return jsonify({"erro": str(erro)}), erro.status

    @app.errorhandler(HTTPException)
    def erro_http(erro: HTTPException):
        return jsonify({"erro": erro.description}), erro.code

    return app


def corpo_json() -> dict:
    """Corpo JSON da requisição atual (ou erro 400 se ausente)."""
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ErroNegocio("Envie um corpo JSON (objeto).")
    return dados


def _enviar_heartbeats(nome: str, porta: int, descricao: str) -> None:
    """Registra o serviço no registro e repete a cada INTERVALO_HEARTBEAT segundos."""
    dados = {"nome": nome, "url": f"http://{config.HOST}:{porta}", "porta": porta,
             "descricao": descricao, "pid": os.getpid()}
    url = f"{config.url_padrao('registro')}/servicos"
    while True:
        try:
            requests.post(url, json=dados, timeout=2)
        except requests.RequestException:
            pass  # registro ainda não subiu; tenta de novo no próximo ciclo
        time.sleep(config.INTERVALO_HEARTBEAT)


def iniciar(app: Flask, registrar: bool = True) -> None:
    """Sobe o microsserviço na porta configurada e inicia os heartbeats."""
    nome = app.config["SCIEVENT_NOME"]
    porta = config.porta(nome)
    logging.basicConfig(level=logging.INFO, format=f"[{nome}] %(levelname)s %(message)s")
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    if registrar:
        threading.Thread(target=_enviar_heartbeats,
                         args=(nome, porta, app.config["SCIEVENT_DESCRICAO"]),
                         daemon=True).start()
    print(f"[{nome}] ouvindo em http://{config.HOST}:{porta}", flush=True)
    app.run(host=config.HOST, port=porta, debug=False, use_reloader=False, threaded=True)
