"""
Microsserviço NOTIFICAÇÕES — porta 5005 — banco: data/notificacoes.db (SQLite).

Recebe as mensagens já formatadas pelo componente de canal do framework e
"envia" (o envio de e-mail é simulado: a mensagem é gravada e aparece no
log do serviço). Assim o sistema roda sem configurar um servidor SMTP.

Estrutura interna (componente com interface):
    Controlador (rotas Flask) -> INotificacaoRepositorio -> NotificacaoRepositorioSQLite

Endpoints:
    POST /notificacoes                       registra e envia uma notificação
    GET  /notificacoes?evento_id=<id>        lista as notificações de um evento
"""
from __future__ import annotations

import logging
import os
import sys
from abc import ABC, abstractmethod

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from flask import jsonify, request  # noqa: E402

from scievent.chassi import (BancoSQLite, ErroNegocio, agora, corpo_json,  # noqa: E402
                             criar_microsservico, iniciar)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS notificacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    canal TEXT NOT NULL,           -- email | mural | ...
    tipo TEXT NOT NULL,            -- submissao_recebida | convite_revisao | decisao | programacao_publicada
    destinatario TEXT NOT NULL,
    assunto TEXT NOT NULL,
    corpo TEXT NOT NULL,
    enviado_em TEXT NOT NULL
);
"""

log = logging.getLogger("notificacoes")


class INotificacaoRepositorio(ABC):
    """Interface do componente de persistência de notificações."""

    @abstractmethod
    def registrar(self, dados: dict) -> dict: ...

    @abstractmethod
    def listar(self, evento_id: int) -> list[dict]: ...


class NotificacaoRepositorioSQLite(INotificacaoRepositorio):
    def __init__(self):
        self.db = BancoSQLite("notificacoes", ESQUEMA)

    def registrar(self, dados: dict) -> dict:
        novo_id = self.db.executar(
            "INSERT INTO notificacoes (evento_id, canal, tipo, destinatario, assunto, corpo, enviado_em)"
            " VALUES (?,?,?,?,?,?,?)",
            (dados["evento_id"], dados["canal"], dados["tipo"], dados["destinatario"],
             dados["assunto"], dados["corpo"], agora()))
        return self.db.consultar("SELECT * FROM notificacoes WHERE id = ?", (novo_id,))[0]

    def listar(self, evento_id: int) -> list[dict]:
        return self.db.consultar("SELECT * FROM notificacoes WHERE evento_id = ? ORDER BY id DESC", (evento_id,))


app = criar_microsservico("notificacoes", "Envio e histórico de notificações (e-mail simulado ou mural)")
repositorio: INotificacaoRepositorio = NotificacaoRepositorioSQLite()


@app.post("/notificacoes")
def enviar_notificacao():
    dados = corpo_json()
    for campo in ("evento_id", "canal", "tipo", "destinatario", "assunto", "corpo"):
        if not dados.get(campo):
            raise ErroNegocio(f"Campo obrigatório ausente: {campo}")
    registrada = repositorio.registrar(dados)
    log.info("[%s] para %s: %s", registrada["canal"], registrada["destinatario"], registrada["assunto"])
    return jsonify(registrada), 201


@app.get("/notificacoes")
def listar_notificacoes():
    evento_id = request.args.get("evento_id", type=int)
    if evento_id is None:
        raise ErroNegocio("Informe o parâmetro evento_id.")
    return jsonify(repositorio.listar(evento_id))


if __name__ == "__main__":
    iniciar(app)
