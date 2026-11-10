"""Implementações do componente de Alocação de Revisores."""
from __future__ import annotations

from typing import Optional

from scievent.interfaces import IEstrategiaAlocacao


def _minusculas(itens) -> set[str]:
    return {str(i).strip().lower() for i in (itens or []) if str(i).strip()}


class AlocacaoPorAfinidade(IEstrategiaAlocacao):
    """
    Escolhe, para cada trabalho, os revisores com maior afinidade de tema.

    Afinidade = 3 pontos se a trilha do trabalho está entre as áreas do
    revisor + 1 ponto por palavra-chave em comum. Empates são desfeitos pela
    menor carga de trabalho. Revisores que são autores, ou da mesma
    instituição de algum autor, são excluídos (conflito de interesse).
    """

    def __init__(self, revisores_por_trabalho: int = 3, evitar_mesma_instituicao: bool = True):
        self.n = revisores_por_trabalho
        self.evitar_mesma_instituicao = evitar_mesma_instituicao

    def descricao(self) -> str:
        return (f"{self.n} revisores por trabalho, escolhidos por afinidade de tema, "
                f"sem conflito de interesse e com carga balanceada")

    @staticmethod
    def afinidade(submissao: dict, revisor: dict) -> int:
        pontos = 3 if submissao.get("trilha") in (revisor.get("areas") or []) else 0
        comuns = _minusculas(submissao.get("palavras_chave")) & _minusculas(revisor.get("palavras_chave"))
        return pontos + len(comuns)

    def alocar(self, submissoes, revisores, carga_atual: Optional[dict] = None) -> list[dict]:
        carga = {r["id"]: (carga_atual or {}).get(r["id"], 0) for r in revisores}
        pares: list[dict] = []
        for sub in submissoes:
            emails = _minusculas(a.get("email") for a in sub.get("autores", []))
            insts = _minusculas(a.get("instituicao") for a in sub.get("autores", []))
            candidatos = []
            for r in revisores:
                if r["email"].lower() in emails:
                    continue
                if self.evitar_mesma_instituicao and r.get("instituicao", "").lower() in insts:
                    continue
                af = self.afinidade(sub, r)
                candidatos.append((-af, carga[r["id"]], r["id"], af))
            candidatos.sort()
            for _, _, revisor_id, af in candidatos[: self.n]:
                pares.append({"submissao_id": sub["id"], "revisor_id": revisor_id, "afinidade": af})
                carga[revisor_id] += 1
        return pares


class AlocacaoRoundRobin(IEstrategiaAlocacao):
    """
    Rodízio simples: cada trabalho vai para o próximo revisor da fila,
    começando pelos menos carregados. Só evita que alguém revise o próprio trabalho.
    """

    def __init__(self, revisores_por_trabalho: int = 1):
        self.n = revisores_por_trabalho

    def descricao(self) -> str:
        return f"Rodízio entre os revisores, {self.n} por trabalho"

    def alocar(self, submissoes, revisores, carga_atual: Optional[dict] = None) -> list[dict]:
        if not revisores:
            return []
        carga = carga_atual or {}
        fila = sorted(revisores, key=lambda r: (carga.get(r["id"], 0), r["id"]))
        pares: list[dict] = []
        posicao = 0
        for sub in submissoes:
            emails = _minusculas(a.get("email") for a in sub.get("autores", []))
            escolhidos: list[int] = []
            tentativas = 0
            while len(escolhidos) < self.n and tentativas < len(fila):
                r = fila[posicao % len(fila)]
                posicao += 1
                tentativas += 1
                if r["email"].lower() not in emails and r["id"] not in escolhidos:
                    escolhidos.append(r["id"])
            pares += [{"submissao_id": sub["id"], "revisor_id": rid, "afinidade": 0} for rid in escolhidos]
        return pares
