"""
Microsserviço REVISÕES — porta 5003 — banco: data/revisoes.db (SQLite).

Guarda o comitê de revisores, as alocações (qual revisor avalia qual
trabalho) e as revisões entregues. A regra de alocação e o formulário NÃO
ficam aqui: são componentes plugados no framework (hotspots); este serviço
apenas persiste o resultado.

Estrutura interna (componente com interface):
    Controlador (rotas Flask) -> IRevisaoRepositorio -> RevisaoRepositorioSQLite

Endpoints:
    POST /revisores                                   cadastra um revisor
    GET  /revisores?evento_id=<id>                    lista os revisores do evento
    POST /alocacoes                                   grava um lote de alocações
    GET  /alocacoes?evento_id|submissao_id|revisor_id|status
    POST /revisoes                                    registra a revisão de uma alocação
    GET  /revisoes?evento_id|submissao_id             lista revisões
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
CREATE TABLE IF NOT EXISTS revisores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    instituicao TEXT,
    areas TEXT NOT NULL,            -- JSON: nomes de trilhas
    palavras_chave TEXT NOT NULL,   -- JSON
    criado_em TEXT NOT NULL,
    UNIQUE (evento_id, email)
);
CREATE TABLE IF NOT EXISTS alocacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    submissao_id INTEGER NOT NULL,
    revisor_id INTEGER NOT NULL REFERENCES revisores(id),
    afinidade INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pendente',   -- pendente | concluida
    criado_em TEXT NOT NULL,
    UNIQUE (submissao_id, revisor_id)
);
CREATE TABLE IF NOT EXISTS revisoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alocacao_id INTEGER NOT NULL UNIQUE REFERENCES alocacoes(id),
    evento_id INTEGER NOT NULL,
    submissao_id INTEGER NOT NULL,
    revisor_id INTEGER NOT NULL,
    respostas TEXT NOT NULL,        -- JSON: {criterio: valor}
    comentario TEXT,
    nota REAL NOT NULL,
    criado_em TEXT NOT NULL
);
"""

SQL_ALOCACOES = """
SELECT a.*, r.nome AS revisor_nome, r.email AS revisor_email
FROM alocacoes a JOIN revisores r ON r.id = a.revisor_id
"""
SQL_REVISOES = """
SELECT v.*, r.nome AS revisor_nome
FROM revisoes v JOIN revisores r ON r.id = v.revisor_id
"""


def _filtros(sql: str, filtros: dict, prefixo: str) -> tuple[str, list]:
    condicoes = [f"{prefixo}.{campo} = ?" for campo, valor in filtros.items() if valor is not None]
    valores = [valor for valor in filtros.values() if valor is not None]
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    return sql + f" ORDER BY {prefixo}.id", valores


class IRevisaoRepositorio(ABC):
    """Interface do componente de persistência do processo de revisão."""

    @abstractmethod
    def criar_revisor(self, dados: dict) -> dict: ...

    @abstractmethod
    def listar_revisores(self, evento_id: int) -> list[dict]: ...

    @abstractmethod
    def criar_alocacoes(self, evento_id: int, pares: list[dict]) -> list[dict]: ...

    @abstractmethod
    def listar_alocacoes(self, filtros: dict) -> list[dict]: ...

    @abstractmethod
    def registrar_revisao(self, dados: dict) -> dict: ...

    @abstractmethod
    def listar_revisoes(self, filtros: dict) -> list[dict]: ...


class RevisaoRepositorioSQLite(IRevisaoRepositorio):
    def __init__(self):
        self.db = BancoSQLite("revisoes", ESQUEMA)

    @staticmethod
    def _revisor(linha: dict) -> dict:
        linha["areas"] = de_json(linha["areas"], [])
        linha["palavras_chave"] = de_json(linha["palavras_chave"], [])
        return linha

    def criar_revisor(self, dados: dict) -> dict:
        existentes = self.db.consultar("SELECT id FROM revisores WHERE evento_id = ? AND email = ?",
                                       (dados["evento_id"], dados["email"]))
        if existentes:
            raise ErroNegocio("Já existe um revisor com este e-mail no evento.", 409)
        novo_id = self.db.executar(
            "INSERT INTO revisores (evento_id, nome, email, instituicao, areas, palavras_chave, criado_em)"
            " VALUES (?,?,?,?,?,?,?)",
            (dados["evento_id"], dados["nome"], dados["email"], dados.get("instituicao", ""),
             para_json(dados.get("areas", [])), para_json(dados.get("palavras_chave", [])), agora()))
        return self._revisor(self.db.consultar("SELECT * FROM revisores WHERE id = ?", (novo_id,))[0])

    def listar_revisores(self, evento_id: int) -> list[dict]:
        linhas = self.db.consultar("SELECT * FROM revisores WHERE evento_id = ? ORDER BY id", (evento_id,))
        return [self._revisor(linha) for linha in linhas]

    def criar_alocacoes(self, evento_id: int, pares: list[dict]) -> list[dict]:
        criadas = []
        for par in pares:
            ja = self.db.consultar("SELECT id FROM alocacoes WHERE submissao_id = ? AND revisor_id = ?",
                                   (par["submissao_id"], par["revisor_id"]))
            if ja:
                continue
            criadas.append(self.db.executar(
                "INSERT INTO alocacoes (evento_id, submissao_id, revisor_id, afinidade, criado_em)"
                " VALUES (?,?,?,?,?)",
                (evento_id, par["submissao_id"], par["revisor_id"], par.get("afinidade", 0), agora())))
        if not criadas:
            return []
        marcadores = ",".join("?" * len(criadas))
        return self.db.consultar(SQL_ALOCACOES + f" WHERE a.id IN ({marcadores}) ORDER BY a.id", criadas)

    def listar_alocacoes(self, filtros: dict) -> list[dict]:
        sql, valores = _filtros(SQL_ALOCACOES, filtros, "a")
        return self.db.consultar(sql, valores)

    def registrar_revisao(self, dados: dict) -> dict:
        alocacao = self.db.consultar("SELECT * FROM alocacoes WHERE id = ?", (dados["alocacao_id"],))
        if not alocacao:
            raise ErroNegocio("Alocação não encontrada.", 404)
        alocacao = alocacao[0]
        if alocacao["status"] == "concluida":
            raise ErroNegocio("Esta alocação já tem revisão registrada.", 409)
        novo_id = self.db.executar(
            "INSERT INTO revisoes (alocacao_id, evento_id, submissao_id, revisor_id, respostas,"
            " comentario, nota, criado_em) VALUES (?,?,?,?,?,?,?,?)",
            (alocacao["id"], alocacao["evento_id"], alocacao["submissao_id"], alocacao["revisor_id"],
             para_json(dados["respostas"]), dados.get("comentario", ""), float(dados["nota"]), agora()))
        self.db.executar("UPDATE alocacoes SET status = 'concluida' WHERE id = ?", (alocacao["id"],))
        return self.listar_revisoes({"id": novo_id})[0]

    def listar_revisoes(self, filtros: dict) -> list[dict]:
        sql, valores = _filtros(SQL_REVISOES, filtros, "v")
        linhas = self.db.consultar(sql, valores)
        for linha in linhas:
            linha["respostas"] = de_json(linha["respostas"], {})
        return linhas


app = criar_microsservico("revisoes", "Revisores, alocações e avaliações dos trabalhos")
repositorio: IRevisaoRepositorio = RevisaoRepositorioSQLite()


@app.post("/revisores")
def criar_revisor():
    dados = corpo_json()
    for campo in ("evento_id", "nome", "email"):
        if not dados.get(campo):
            raise ErroNegocio(f"Campo obrigatório ausente: {campo}")
    return jsonify(repositorio.criar_revisor(dados)), 201


@app.get("/revisores")
def listar_revisores():
    evento_id = request.args.get("evento_id", type=int)
    if evento_id is None:
        raise ErroNegocio("Informe o parâmetro evento_id.")
    return jsonify(repositorio.listar_revisores(evento_id))


@app.post("/alocacoes")
def criar_alocacoes():
    dados = corpo_json()
    if "evento_id" not in dados or not isinstance(dados.get("alocacoes"), list):
        raise ErroNegocio("Envie {'evento_id': .., 'alocacoes': [{'submissao_id', 'revisor_id'}]}")
    return jsonify(repositorio.criar_alocacoes(dados["evento_id"], dados["alocacoes"])), 201


@app.get("/alocacoes")
def listar_alocacoes():
    filtros = {"evento_id": request.args.get("evento_id", type=int),
               "submissao_id": request.args.get("submissao_id", type=int),
               "revisor_id": request.args.get("revisor_id", type=int),
               "status": request.args.get("status")}
    return jsonify(repositorio.listar_alocacoes(filtros))


@app.post("/revisoes")
def registrar_revisao():
    dados = corpo_json()
    for campo in ("alocacao_id", "respostas", "nota"):
        if campo not in dados:
            raise ErroNegocio(f"Campo obrigatório ausente: {campo}")
    return jsonify(repositorio.registrar_revisao(dados)), 201


@app.get("/revisoes")
def listar_revisoes():
    filtros = {"evento_id": request.args.get("evento_id", type=int),
               "submissao_id": request.args.get("submissao_id", type=int)}
    return jsonify(repositorio.listar_revisoes(filtros))


if __name__ == "__main__":
    iniciar(app)
