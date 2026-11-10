"""Implementações do componente de Validação de Submissão."""
from __future__ import annotations

import re

from scievent.interfaces import IValidadorSubmissao


def contar_palavras(texto: str) -> int:
    return len(re.findall(r"\w+", texto or "", flags=re.UNICODE))


class ValidadorRigoroso(IValidadorSubmissao):
    """
    Regras de um congresso com revisão duplo-cega:
    resumo com tamanho mínimo e máximo, número fixo de palavras-chave,
    trilha obrigatória, dados completos de cada autor e anonimato
    (o nome dos autores não pode aparecer no título nem no resumo).
    """

    def __init__(self, min_palavras: int = 50, max_palavras: int = 300,
                 min_palavras_chave: int = 3, max_palavras_chave: int = 5,
                 max_autores: int = 8):
        self.min_palavras = min_palavras
        self.max_palavras = max_palavras
        self.min_kw = min_palavras_chave
        self.max_kw = max_palavras_chave
        self.max_autores = max_autores

    def descricao(self) -> str:
        return (f"Resumo de {self.min_palavras} a {self.max_palavras} palavras, "
                f"{self.min_kw} a {self.max_kw} palavras-chave, trilha obrigatória "
                f"e texto anonimizado")

    def validar(self, submissao: dict, evento: dict) -> list[str]:
        erros: list[str] = []
        titulo = (submissao.get("titulo") or "").strip()
        resumo = submissao.get("resumo") or ""
        kws = submissao.get("palavras_chave") or []
        autores = submissao.get("autores") or []

        if not 10 <= len(titulo) <= 200:
            erros.append("O título deve ter entre 10 e 200 caracteres.")

        n = contar_palavras(resumo)
        if not self.min_palavras <= n <= self.max_palavras:
            erros.append(f"O resumo tem {n} palavras; o evento exige entre "
                         f"{self.min_palavras} e {self.max_palavras}.")

        if not self.min_kw <= len(kws) <= self.max_kw:
            erros.append(f"Informe de {self.min_kw} a {self.max_kw} palavras-chave "
                         f"(recebidas: {len(kws)}).")

        trilhas = [t["nome"] for t in evento.get("trilhas", [])]
        if submissao.get("trilha") not in trilhas:
            erros.append("Escolha uma das trilhas do evento: " + ", ".join(trilhas) + ".")

        if not 1 <= len(autores) <= self.max_autores:
            erros.append(f"O trabalho deve ter de 1 a {self.max_autores} autores.")
        for i, autor in enumerate(autores, start=1):
            faltando = [c for c in ("nome", "email", "instituicao") if not autor.get(c)]
            if faltando:
                erros.append(f"Autor {i}: preencha " + ", ".join(faltando) + ".")
            elif "@" not in autor["email"]:
                erros.append(f"Autor {i}: e-mail inválido.")

        # Revisão duplo-cega: o texto avaliado não pode identificar os autores.
        texto = f"{titulo} {resumo}".lower()
        for autor in autores:
            nome = (autor.get("nome") or "").strip().lower()
            if len(nome) > 3 and nome in texto:
                erros.append(f"Anonimato: o nome '{autor['nome']}' aparece no título "
                             f"ou no resumo. Remova-o (revisão duplo-cega).")
        return erros


class ValidadorSimples(IValidadorSubmissao):
    """
    Regras de uma jornada de iniciação científica: só o essencial.
    Título e resumo preenchidos, resumo até um limite de palavras e
    ao menos um autor com nome e e-mail.
    """

    def __init__(self, max_palavras: int = 500):
        self.max_palavras = max_palavras

    def descricao(self) -> str:
        return f"Título, resumo de até {self.max_palavras} palavras e um autor com e-mail"

    def validar(self, submissao: dict, evento: dict) -> list[str]:
        erros: list[str] = []
        if not (submissao.get("titulo") or "").strip():
            erros.append("Informe o título do trabalho.")
        n = contar_palavras(submissao.get("resumo") or "")
        if n == 0:
            erros.append("Informe o resumo do trabalho.")
        elif n > self.max_palavras:
            erros.append(f"O resumo tem {n} palavras; o limite é {self.max_palavras}.")
        autores = submissao.get("autores") or []
        if not autores or not autores[0].get("nome") or "@" not in (autores[0].get("email") or ""):
            erros.append("Informe ao menos um autor com nome e e-mail válidos.")
        return erros
