"""Implementações do componente de Geração de Programação."""
from __future__ import annotations

import random
from collections import defaultdict

from scievent.interfaces import IGeradorProgramacao
from scievent.modelos import Apresentacao, Programa, Sessao, hhmm, minutos


def _apresentacao(sub: dict, inicio: int, fim: int) -> Apresentacao:
    autores = sub.get("autores", [])
    return Apresentacao(
        submissao_id=sub["id"],
        titulo=sub["titulo"],
        autores=", ".join(a["nome"] for a in autores),
        autores_emails=[a["email"].lower() for a in autores],
        trilha=sub.get("trilha") or "",
        inicio=hhmm(inicio),
        fim=hhmm(fim),
    )


def _em_blocos(itens: list, tamanho: int) -> list[list]:
    return [itens[i:i + tamanho] for i in range(0, len(itens), tamanho)]


class ProgramacaoPorTrilhas(IGeradorProgramacao):
    """
    Sessões temáticas em salas paralelas: cada trilha vira uma ou mais sessões
    com N trabalhos; sessões de um mesmo horário ocupam salas diferentes.
    Pôsteres ficam numa sessão própria ao final.

    Conflito: um mesmo autor apresentando em duas salas no mesmo horário.
    A partir da 2ª tentativa as sessões são embaralhadas (semente = tentativa),
    o que normalmente resolve o conflito.
    """

    def __init__(self, salas=("Auditório A", "Sala 101", "Sala 102"), artigos_por_sessao: int = 3,
                 duracao_min: int = 20, inicio: str = "09:00", intervalo_min: int = 15,
                 sala_posteres: str = "Hall de Exposições"):
        self.salas = list(salas)
        self.artigos_por_sessao = artigos_por_sessao
        self.duracao = duracao_min
        self.inicio = inicio
        self.intervalo = intervalo_min
        self.sala_posteres = sala_posteres

    def descricao(self) -> str:
        return (f"Sessões temáticas por trilha em {len(self.salas)} salas paralelas, "
                f"{self.artigos_por_sessao} trabalhos de {self.duracao} min por sessão")

    def gerar(self, aceitos, evento, tentativa) -> Programa:
        orais = [s for s in aceitos if (s.get("decisao") or {}).get("modalidade") != "poster"]
        posteres = [s for s in aceitos if (s.get("decisao") or {}).get("modalidade") == "poster"]

        ordem_trilhas = [t["nome"] for t in evento.get("trilhas", [])]
        por_trilha: dict[str, list] = defaultdict(list)
        for s in sorted(orais, key=lambda s: s["id"]):
            por_trilha[s.get("trilha") or "Geral"].append(s)
        trilhas = sorted(por_trilha, key=lambda t: ordem_trilhas.index(t) if t in ordem_trilhas else 99)

        blocos = []
        for trilha in trilhas:
            partes = _em_blocos(por_trilha[trilha], self.artigos_por_sessao)
            for k, parte in enumerate(partes, start=1):
                titulo = trilha if len(partes) == 1 else f"{trilha} ({k})"
                blocos.append((trilha, titulo, parte))
        if tentativa > 1:
            random.Random(tentativa).shuffle(blocos)

        sessoes: list[Sessao] = []
        duracao_slot = self.artigos_por_sessao * self.duracao
        for idx, (trilha, titulo, parte) in enumerate(blocos):
            slot, sala = divmod(idx, len(self.salas))
            inicio = minutos(self.inicio) + slot * (duracao_slot + self.intervalo)
            sessao = Sessao(titulo, self.salas[sala], hhmm(inicio), hhmm(inicio + duracao_slot), trilha)
            for j, sub in enumerate(parte):
                ini = inicio + j * self.duracao
                sessao.apresentacoes.append(_apresentacao(sub, ini, ini + self.duracao))
            sessoes.append(sessao)

        if posteres:
            n_slots = -(-len(blocos) // len(self.salas))  # divisão arredondando para cima
            inicio = minutos(self.inicio) + n_slots * (duracao_slot + self.intervalo)
            sessao = Sessao("Sessão de Pôsteres", self.sala_posteres, hhmm(inicio), hhmm(inicio + 60), "Pôsteres")
            sessao.apresentacoes = [_apresentacao(s, inicio, inicio + 60) for s in posteres]
            sessoes.append(sessao)

        obs = [f"{len(orais)} apresentações orais em {len(blocos)} sessões paralelas "
               f"({len(self.salas)} salas) e {len(posteres)} pôsteres."]
        return Programa(sessoes, obs)

    def verificar_conflitos(self, programa: Programa) -> list[str]:
        por_horario: dict[str, list[Sessao]] = defaultdict(list)
        for s in programa.sessoes:
            por_horario[s.inicio].append(s)
        conflitos = []
        for inicio, sessoes in sorted(por_horario.items()):
            onde: dict[str, Sessao] = {}
            for s in sessoes:
                for email in {e for a in s.apresentacoes for e in a.autores_emails}:
                    if email in onde:
                        outra = onde[email]
                        conflitos.append(f"{email} apresenta às {inicio} em '{outra.titulo}' "
                                         f"({outra.sala}) e em '{s.titulo}' ({s.sala}).")
                    else:
                        onde[email] = s
        return conflitos


class ProgramacaoSequencial(IGeradorProgramacao):
    """
    Uma única sala, apresentações em sequência, organizadas em blocos com
    intervalo entre eles. Conflito: a programação passar do horário limite.
    """

    def __init__(self, sala: str = "Auditório Principal", duracao_min: int = 15,
                 inicio: str = "14:00", apresentacoes_por_bloco: int = 4,
                 intervalo_min: int = 20, horario_limite: str = "18:00"):
        self.sala = sala
        self.duracao = duracao_min
        self.inicio = inicio
        self.por_bloco = apresentacoes_por_bloco
        self.intervalo = intervalo_min
        self.limite = horario_limite

    def descricao(self) -> str:
        return (f"Sala única ({self.sala}), apresentações de {self.duracao} min em "
                f"blocos de {self.por_bloco} com intervalo, até as {self.limite}")

    def gerar(self, aceitos, evento, tentativa) -> Programa:
        ordenados = sorted(aceitos, key=lambda s: (s.get("trilha") or "", s["id"]))
        relogio = minutos(self.inicio)
        sessoes = []
        for k, bloco in enumerate(_em_blocos(ordenados, self.por_bloco), start=1):
            sessao = Sessao(f"Bloco {k}", self.sala, hhmm(relogio),
                            hhmm(relogio + len(bloco) * self.duracao), "Todas")
            for sub in bloco:
                sessao.apresentacoes.append(_apresentacao(sub, relogio, relogio + self.duracao))
                relogio += self.duracao
            sessoes.append(sessao)
            relogio += self.intervalo
        obs = [f"{len(ordenados)} apresentações em sala única, {len(sessoes)} blocos "
               f"com {self.intervalo} min de intervalo."]
        return Programa(sessoes, obs)

    def verificar_conflitos(self, programa: Programa) -> list[str]:
        if programa.sessoes and minutos(programa.sessoes[-1].fim) > minutos(self.limite):
            return [f"A programação termina às {programa.sessoes[-1].fim}, depois do limite das {self.limite}."]
        return []
