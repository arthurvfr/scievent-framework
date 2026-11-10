"""
Microsserviço EVENTOS — porta 5001 — banco: data/eventos.db (SQLite).

Guarda cada evento criado por uma aplicação do framework: nome, datas,
trilhas temáticas e quais componentes a aplicação plugou em cada hotspot.

Estrutura interna (componente com interface):
    Controlador (rotas Flask) -> IEventoRepositorio -> EventoRepositorioSQLite

Endpoints:
    POST /eventos                     cria um evento
    GET  /eventos[?aplicacao=<id>]    lista eventos (opcionalmente de uma aplicação)
    GET  /eventos/<id>                obtém um evento
"""
from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from flask import jsonify, request  # noqa: E402

from scievent.chassi import (BancoSQLite, ErroNegocio, agora, corpo_json,  # noqa: E402
                             criar_microsservico, de_json, iniciar, para_json)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aplicacao TEXT NOT NULL,
    nome TEXT NOT NULL,
    sigla TEXT NOT NULL,
    descricao TEXT,
    local TEXT,
    data_inicio TEXT,
    data_fim TEXT,
    trilhas TEXT NOT NULL,        -- JSON: [{"nome", "palavras_chave": [..]}]
    componentes TEXT NOT NULL,    -- JSON: [{"hotspot", "componente", "descricao"}]
    criado_em TEXT NOT NULL
);
"""


class IEventoRepositorio(ABC):
    """Interface do componente de persistência de eventos."""

    @abstractmethod
    def criar(self, dados: dict) -> dict: ...

    @abstractmethod
    def obter(self, evento_id: int) -> dict | None: ...

    @abstractmethod
    def listar(self, aplicacao: str | None = None) -> list[dict]: ...


class EventoRepositorioSQLite(IEventoRepositorio):
    def __init__(self):
        self.db = BancoSQLite("eventos", ESQUEMA)

    @staticmethod
    def _converter(linha: dict) -> dict:
        linha["trilhas"] = de_json(linha["trilhas"], [])
        linha["componentes"] = de_json(linha["componentes"], [])
        return linha

    def criar(self, dados: dict) -> dict:
        novo_id = self.db.executar(
            "INSERT INTO eventos (aplicacao, nome, sigla, descricao, local, data_inicio, data_fim,"
            " trilhas, componentes, criado_em) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (dados["aplicacao"], dados["nome"], dados["sigla"], dados.get("descricao", ""),
             dados.get("local", ""), dados.get("data_inicio", ""), dados.get("data_fim", ""),
             para_json(dados.get("trilhas", [])), para_json(dados.get("componentes", [])), agora()))
        return self.obter(novo_id)

    def obter(self, evento_id: int) -> dict | None:
        linhas = self.db.consultar("SELECT * FROM eventos WHERE id = ?", (evento_id,))
        return self._converter(linhas[0]) if linhas else None

    def listar(self, aplicacao: str | None = None) -> list[dict]:
        if aplicacao:
            linhas = self.db.consultar("SELECT * FROM eventos WHERE aplicacao = ? ORDER BY id", (aplicacao,))
        else:
            linhas = self.db.consultar("SELECT * FROM eventos ORDER BY id")
        return [self._converter(linha) for linha in linhas]


app = criar_microsservico("eventos", "Eventos, trilhas temáticas e componentes em uso")
repositorio: IEventoRepositorio = EventoRepositorioSQLite()


@app.post("/eventos")
def criar_evento():
    dados = corpo_json()
    for campo in ("aplicacao", "nome", "sigla"):
        if not dados.get(campo):
            raise ErroNegocio(f"Campo obrigatório ausente: {campo}")
    return jsonify(repositorio.criar(dados)), 201


@app.get("/eventos")
def listar_eventos():
    return jsonify(repositorio.listar(request.args.get("aplicacao")))


@app.get("/eventos/<int:evento_id>")
def obter_evento(evento_id):
    evento = repositorio.obter(evento_id)
    if not evento:
        raise ErroNegocio("Evento não encontrado.", 404)
    return jsonify(evento)


if __name__ == "__main__":
    iniciar(app)
