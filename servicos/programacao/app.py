"""
Microsserviço PROGRAMAÇÃO — porta 5004 — banco: data/programacao.db (SQLite).

Publica a grade do evento gerada pelo componente de programação do
framework. Guarda a versão mais recente de cada evento, com o histórico de
tentativas e eventuais conflitos.

Estrutura interna (componente com interface):
    Controlador (rotas Flask) -> IProgramacaoRepositorio -> ProgramacaoRepositorioSQLite

Endpoints:
    PUT /programacao/<evento_id>    grava (ou substitui) a programação do evento
    GET /programacao/<evento_id>    obtém a programação publicada
"""
from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from flask import jsonify  # noqa: E402

from scievent.chassi import (BancoSQLite, ErroNegocio, agora, corpo_json,  # noqa: E402
                             criar_microsservico, de_json, iniciar, para_json)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS programas (
    evento_id INTEGER PRIMARY KEY,
    conteudo TEXT NOT NULL,     -- JSON: {"sessoes", "observacoes", "tentativas", "conflitos"}
    publicado_em TEXT NOT NULL
);
"""


class IProgramacaoRepositorio(ABC):
    """Interface do componente de persistência da programação."""

    @abstractmethod
    def salvar(self, evento_id: int, programa: dict) -> dict: ...

    @abstractmethod
    def obter(self, evento_id: int) -> dict | None: ...


class ProgramacaoRepositorioSQLite(IProgramacaoRepositorio):
    def __init__(self):
        self.db = BancoSQLite("programacao", ESQUEMA)

    def salvar(self, evento_id: int, programa: dict) -> dict:
        self.db.executar(
            "INSERT INTO programas (evento_id, conteudo, publicado_em) VALUES (?,?,?)"
            " ON CONFLICT(evento_id) DO UPDATE SET conteudo = excluded.conteudo,"
            " publicado_em = excluded.publicado_em",
            (evento_id, para_json(programa), agora()))
        return self.obter(evento_id)

    def obter(self, evento_id: int) -> dict | None:
        linhas = self.db.consultar("SELECT * FROM programas WHERE evento_id = ?", (evento_id,))
        if not linhas:
            return None
        return {"evento_id": evento_id, "publicado_em": linhas[0]["publicado_em"],
                **de_json(linhas[0]["conteudo"], {})}


app = criar_microsservico("programacao", "Grade de sessões publicada de cada evento")
repositorio: IProgramacaoRepositorio = ProgramacaoRepositorioSQLite()


@app.put("/programacao/<int:evento_id>")
def salvar_programacao(evento_id):
    programa = corpo_json()
    if not isinstance(programa.get("sessoes"), list):
        raise ErroNegocio("A programação precisa ter a lista 'sessoes'.")
    return jsonify(repositorio.salvar(evento_id, programa))


@app.get("/programacao/<int:evento_id>")
def obter_programacao(evento_id):
    programa = repositorio.obter(evento_id)
    if not programa:
        raise ErroNegocio("Programação ainda não gerada para este evento.", 404)
    return jsonify(programa)


if __name__ == "__main__":
    iniciar(app)
