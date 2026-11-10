"""
Microsserviço SUBMISSÕES — porta 5002 — banco: data/submissoes.db (SQLite).

Guarda os trabalhos submetidos e o ciclo de vida de cada um:
    submetida -> em_revisao -> aceito | rejeitado

Estrutura interna (componente com interface):
    Controlador (rotas Flask) -> ISubmissaoRepositorio -> SubmissaoRepositorioSQLite

Endpoints:
    POST  /submissoes                                  cria uma submissão (status 'submetida')
    GET   /submissoes?evento_id=<id>[&status=<s>]      lista as submissões de um evento
    GET   /submissoes/<id>                             obtém uma submissão
    PATCH /submissoes/<id>                             altera status, decisão, triagem ou parecer
"""
from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from flask import jsonify, request  # noqa: E402

from scievent.chassi import (BancoSQLite, ErroNegocio, agora, corpo_json,  # noqa: E402
                             criar_microsservico, de_json, iniciar, para_json)

STATUS_VALIDOS = {"submetida", "em_revisao", "aceito", "rejeitado"}
CAMPOS_JSON = {"palavras_chave", "autores", "decisao", "triagem"}
CAMPOS_ALTERAVEIS = {"status", "decisao", "triagem", "parecer"}

ESQUEMA = """
CREATE TABLE IF NOT EXISTS submissoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    resumo TEXT NOT NULL,
    palavras_chave TEXT NOT NULL,   -- JSON
    trilha TEXT,
    autores TEXT NOT NULL,          -- JSON: [{"nome", "email", "instituicao"}]
    status TEXT NOT NULL DEFAULT 'submetida',
    decisao TEXT,                   -- JSON: {"status", "modalidade", "media", "justificativa"}
    triagem TEXT,                   -- JSON produzido pelo agente de triagem (opcional)
    parecer TEXT,                   -- meta-revisão produzida pelo agente (opcional)
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sub_evento ON submissoes(evento_id, status);
"""


class ISubmissaoRepositorio(ABC):
    """Interface do componente de persistência de submissões."""

    @abstractmethod
    def criar(self, dados: dict) -> dict: ...

    @abstractmethod
    def obter(self, submissao_id: int) -> dict | None: ...

    @abstractmethod
    def listar(self, evento_id: int, status: str | None = None) -> list[dict]: ...

    @abstractmethod
    def atualizar(self, submissao_id: int, campos: dict) -> dict: ...


class SubmissaoRepositorioSQLite(ISubmissaoRepositorio):
    def __init__(self):
        self.db = BancoSQLite("submissoes", ESQUEMA)

    @staticmethod
    def _converter(linha: dict) -> dict:
        for campo in CAMPOS_JSON:
            linha[campo] = de_json(linha[campo], [] if campo in ("palavras_chave", "autores") else None)
        return linha

    def criar(self, dados: dict) -> dict:
        momento = agora()
        novo_id = self.db.executar(
            "INSERT INTO submissoes (evento_id, titulo, resumo, palavras_chave, trilha, autores,"
            " status, criado_em, atualizado_em) VALUES (?,?,?,?,?,?, 'submetida', ?, ?)",
            (dados["evento_id"], dados["titulo"], dados["resumo"], para_json(dados.get("palavras_chave", [])),
             dados.get("trilha", ""), para_json(dados["autores"]), momento, momento))
        return self.obter(novo_id)

    def obter(self, submissao_id: int) -> dict | None:
        linhas = self.db.consultar("SELECT * FROM submissoes WHERE id = ?", (submissao_id,))
        return self._converter(linhas[0]) if linhas else None

    def listar(self, evento_id: int, status: str | None = None) -> list[dict]:
        sql, parametros = "SELECT * FROM submissoes WHERE evento_id = ?", [evento_id]
        if status:
            sql += " AND status = ?"
            parametros.append(status)
        return [self._converter(linha) for linha in self.db.consultar(sql + " ORDER BY id", parametros)]

    def atualizar(self, submissao_id: int, campos: dict) -> dict:
        atribuicoes, valores = [], []
        for campo, valor in campos.items():
            atribuicoes.append(f"{campo} = ?")
            valores.append(para_json(valor) if campo in CAMPOS_JSON else valor)
        valores += [agora(), submissao_id]
        self.db.executar(f"UPDATE submissoes SET {', '.join(atribuicoes)}, atualizado_em = ? WHERE id = ?", valores)
        return self.obter(submissao_id)


app = criar_microsservico("submissoes", "Trabalhos submetidos e seu ciclo de vida")
repositorio: ISubmissaoRepositorio = SubmissaoRepositorioSQLite()


@app.post("/submissoes")
def criar_submissao():
    dados = corpo_json()
    for campo in ("evento_id", "titulo", "resumo", "autores"):
        if not dados.get(campo):
            raise ErroNegocio(f"Campo obrigatório ausente: {campo}")
    return jsonify(repositorio.criar(dados)), 201


@app.get("/submissoes")
def listar_submissoes():
    evento_id = request.args.get("evento_id", type=int)
    if evento_id is None:
        raise ErroNegocio("Informe o parâmetro evento_id.")
    return jsonify(repositorio.listar(evento_id, request.args.get("status")))


@app.get("/submissoes/<int:submissao_id>")
def obter_submissao(submissao_id):
    sub = repositorio.obter(submissao_id)
    if not sub:
        raise ErroNegocio("Submissão não encontrada.", 404)
    return jsonify(sub)


@app.patch("/submissoes/<int:submissao_id>")
def atualizar_submissao(submissao_id):
    if not repositorio.obter(submissao_id):
        raise ErroNegocio("Submissão não encontrada.", 404)
    campos = {k: v for k, v in corpo_json().items() if k in CAMPOS_ALTERAVEIS}
    if not campos:
        raise ErroNegocio("Nada a alterar. Campos aceitos: " + ", ".join(sorted(CAMPOS_ALTERAVEIS)))
    if "status" in campos and campos["status"] not in STATUS_VALIDOS:
        raise ErroNegocio("Status inválido. Use: " + ", ".join(sorted(STATUS_VALIDOS)))
    return jsonify(repositorio.atualizar(submissao_id, campos))


if __name__ == "__main__":
    iniciar(app)
