"""Implementações do componente de Formulário de Avaliação."""
from __future__ import annotations

from typing import Optional

from scievent.interfaces import IFormularioAvaliacao
from scievent.modelos import Criterio

CRITERIOS_PADRAO = [
    Criterio("originalidade", "Originalidade", 0.3, 1, 5, "O trabalho traz contribuição nova?"),
    Criterio("relevancia", "Relevância", 0.2, 1, 5, "O tema interessa à comunidade do evento?"),
    Criterio("metodologia", "Metodologia", 0.3, 1, 5, "O método e a avaliação são adequados?"),
    Criterio("clareza", "Clareza", 0.2, 1, 5, "O texto é claro e bem organizado?"),
]


def _validar_escala(criterios: list[Criterio], respostas: dict) -> list[str]:
    erros = []
    for c in criterios:
        valor = respostas.get(c.chave)
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            erros.append(f"Preencha o critério '{c.rotulo}'.")
            continue
        if not c.minimo <= valor <= c.maximo:
            erros.append(f"'{c.rotulo}' deve estar entre {c.minimo} e {c.maximo}.")
    return erros


class FormularioPonderado(IFormularioAvaliacao):
    """
    Vários critérios com pesos, nota de 1 a 5 em cada um.
    Nota final = média ponderada. Exige comentário justificando a avaliação.
    """

    def __init__(self, criterios: Optional[list[Criterio]] = None, comentario_minimo: int = 30):
        self._criterios = criterios or CRITERIOS_PADRAO
        self.comentario_minimo = comentario_minimo

    def descricao(self) -> str:
        pesos = ", ".join(f"{c.rotulo} {c.peso:.0%}" for c in self._criterios)
        return f"Média ponderada de critérios de 1 a 5 ({pesos}) com comentário obrigatório"

    def criterios(self) -> list[Criterio]:
        return list(self._criterios)

    def validar(self, respostas, comentario) -> list[str]:
        erros = _validar_escala(self._criterios, respostas)
        if len((comentario or "").strip()) < self.comentario_minimo:
            erros.append(f"Escreva um comentário com ao menos {self.comentario_minimo} caracteres.")
        return erros

    def calcular_nota(self, respostas) -> float:
        soma_pesos = sum(c.peso for c in self._criterios)
        total = sum(c.peso * float(respostas[c.chave]) for c in self._criterios)
        return round(total / soma_pesos, 2)


class FormularioNotaUnica(IFormularioAvaliacao):
    """Uma única nota geral (padrão 0 a 10). Comentário opcional."""

    def __init__(self, minimo: int = 0, maximo: int = 10, comentario_minimo: int = 0):
        self._criterio = Criterio("nota", "Nota geral do trabalho", 1.0, minimo, maximo,
                                  "Avalie o trabalho como um todo.")
        self.comentario_minimo = comentario_minimo

    def descricao(self) -> str:
        return f"Nota única de {self._criterio.minimo} a {self._criterio.maximo}"

    def criterios(self) -> list[Criterio]:
        return [self._criterio]

    def validar(self, respostas, comentario) -> list[str]:
        erros = _validar_escala([self._criterio], respostas)
        if len((comentario or "").strip()) < self.comentario_minimo:
            erros.append(f"Escreva um comentário com ao menos {self.comentario_minimo} caracteres.")
        return erros

    def calcular_nota(self, respostas) -> float:
        return round(float(respostas["nota"]), 2)
