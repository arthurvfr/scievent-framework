"""
Clientes HTTP dos microsserviços (frozen spot do framework).

O núcleo do framework nunca monta URLs: ele chama métodos destes clientes.
A URL de cada serviço é descoberta no Service Registry; se o registro não
responder, usa-se o endereço padrão de scievent.config.
"""
from __future__ import annotations

import time
from typing import Callable, Optional

import requests

from scievent import config

# Funções avisadas a cada chamada (o gateway usa isso para mostrar na tela
# quais microsserviços foram usados para montar cada página).
_observadores: list[Callable[[str], None]] = []


def observar_chamadas(funcao: Callable[[str], None]) -> None:
    _observadores.append(funcao)


class ErroServico(Exception):
    """Falha ao falar com um microsserviço (fora do ar ou erro de negócio)."""

    def __init__(self, servico: str, mensagem: str, status: Optional[int] = None):
        super().__init__(f"[{servico}] {mensagem}")
        self.servico = servico
        self.mensagem = mensagem
        self.status = status


class ResolvedorServicos:
    """Descobre o endereço de cada serviço no Service Registry (com cache curto)."""

    def __init__(self, url_registro: Optional[str] = None, ttl: float = 5.0):
        self.url_registro = url_registro or config.url_padrao("registro")
        self.ttl = ttl
        self._cache: dict[str, str] = {}
        self._ultima_consulta = 0.0

    def url(self, nome: str) -> str:
        if nome == "registro":
            return self.url_registro
        if time.monotonic() - self._ultima_consulta > self.ttl:
            self._atualizar()
        return self._cache.get(nome) or config.url_padrao(nome)

    def _atualizar(self) -> None:
        try:
            resposta = requests.get(f"{self.url_registro}/servicos", timeout=1.5)
            self._cache = {s["nome"]: s["url"] for s in resposta.json() if s.get("ativo")}
        except (requests.RequestException, ValueError):
            pass  # sem registro: segue com os endereços padrão
        self._ultima_consulta = time.monotonic()


class ClienteHTTP:
    """Base dos clientes: resolve a URL, faz a chamada e traduz erros."""

    nome = ""
    timeout = config.TIMEOUT_HTTP

    def __init__(self, resolvedor: ResolvedorServicos):
        self.resolvedor = resolvedor

    def _req(self, metodo: str, caminho: str, **kwargs):
        for avisar in _observadores:
            avisar(self.nome)
        url = self.resolvedor.url(self.nome) + caminho
        try:
            resposta = requests.request(metodo, url, timeout=self.timeout, **kwargs)
        except requests.RequestException:
            raise ErroServico(self.nome, f"o microsserviço '{self.nome}' não respondeu em {url}")
        if resposta.status_code >= 400:
            try:
                detalhe = resposta.json().get("erro")
            except ValueError:
                detalhe = resposta.text[:200]
            raise ErroServico(self.nome, detalhe or f"HTTP {resposta.status_code}", resposta.status_code)
        return resposta.json() if resposta.content else None


class ClienteRegistro(ClienteHTTP):
    nome = "registro"

    def listar(self) -> list[dict]:
        return self._req("GET", "/servicos")


class ClienteEventos(ClienteHTTP):
    nome = "eventos"

    def criar(self, dados: dict) -> dict:
        return self._req("POST", "/eventos", json=dados)

    def obter(self, evento_id: int) -> dict:
        return self._req("GET", f"/eventos/{evento_id}")

    def listar(self) -> list[dict]:
        return self._req("GET", "/eventos")

    def buscar_por_aplicacao(self, aplicacao: str) -> list[dict]:
        return self._req("GET", "/eventos", params={"aplicacao": aplicacao})


class ClienteSubmissoes(ClienteHTTP):
    nome = "submissoes"

    def criar(self, dados: dict) -> dict:
        return self._req("POST", "/submissoes", json=dados)

    def listar(self, evento_id: int, status: Optional[str] = None) -> list[dict]:
        params = {"evento_id": evento_id}
        if status:
            params["status"] = status
        return self._req("GET", "/submissoes", params=params)

    def obter(self, submissao_id: int) -> dict:
        return self._req("GET", f"/submissoes/{submissao_id}")

    def atualizar(self, submissao_id: int, **campos) -> dict:
        return self._req("PATCH", f"/submissoes/{submissao_id}", json=campos)


class ClienteRevisoes(ClienteHTTP):
    nome = "revisoes"

    def criar_revisor(self, evento_id: int, dados: dict) -> dict:
        return self._req("POST", "/revisores", json={**dados, "evento_id": evento_id})

    def listar_revisores(self, evento_id: int) -> list[dict]:
        return self._req("GET", "/revisores", params={"evento_id": evento_id})

    def criar_alocacoes(self, evento_id: int, pares: list[dict]) -> list[dict]:
        return self._req("POST", "/alocacoes", json={"evento_id": evento_id, "alocacoes": pares})

    def listar_alocacoes(self, **filtros) -> list[dict]:
        return self._req("GET", "/alocacoes", params={k: v for k, v in filtros.items() if v is not None})

    def registrar_revisao(self, alocacao_id: int, respostas: dict, comentario: str, nota: float) -> dict:
        return self._req("POST", "/revisoes", json={"alocacao_id": alocacao_id, "respostas": respostas,
                                                    "comentario": comentario, "nota": nota})

    def listar_revisoes(self, **filtros) -> list[dict]:
        return self._req("GET", "/revisoes", params={k: v for k, v in filtros.items() if v is not None})


class ClienteProgramacao(ClienteHTTP):
    nome = "programacao"

    def salvar(self, evento_id: int, programa: dict) -> dict:
        return self._req("PUT", f"/programacao/{evento_id}", json=programa)

    def obter(self, evento_id: int) -> Optional[dict]:
        try:
            return self._req("GET", f"/programacao/{evento_id}")
        except ErroServico as erro:
            if erro.status == 404:
                return None
            raise


class ClienteNotificacoes(ClienteHTTP):
    nome = "notificacoes"

    def enviar(self, dados: dict) -> dict:
        return self._req("POST", "/notificacoes", json=dados)

    def listar(self, evento_id: int) -> list[dict]:
        return self._req("GET", "/notificacoes", params={"evento_id": evento_id})


class ClienteAgentes(ClienteHTTP):
    nome = "agentes"
    timeout = 120  # um modelo de linguagem local pode demorar

    def triagem(self, evento: dict, submissao: dict) -> dict:
        return self._req("POST", "/triagem", json={"evento": evento, "submissao": submissao})

    def meta_revisao(self, evento: dict, submissao: dict, revisoes: list, decisao: dict) -> dict:
        return self._req("POST", "/meta-revisao", json={"evento": evento, "submissao": submissao,
                                                        "revisoes": revisoes, "decisao": decisao})

    def pool(self, evento_id: int) -> list[dict]:
        return self._req("GET", "/pool", params={"evento_id": evento_id})

    def papeis(self) -> list[dict]:
        return self._req("GET", "/papeis")

    def modelo(self) -> dict:
        return self._req("GET", "/modelo")


class ServicosSciEvent:
    """Fachada: um cliente pronto para cada microsserviço."""

    def __init__(self, resolvedor: Optional[ResolvedorServicos] = None):
        self.resolvedor = resolvedor or ResolvedorServicos()
        self.registro = ClienteRegistro(self.resolvedor)
        self.eventos = ClienteEventos(self.resolvedor)
        self.submissoes = ClienteSubmissoes(self.resolvedor)
        self.revisoes = ClienteRevisoes(self.resolvedor)
        self.programacao = ClienteProgramacao(self.resolvedor)
        self.notificacoes = ClienteNotificacoes(self.resolvedor)
        self.agentes = ClienteAgentes(self.resolvedor)
