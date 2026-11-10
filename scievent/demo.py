"""
Utilitários de demonstração. NÃO fazem parte do fluxo do framework: servem
para popular uma aplicação com dados de exemplo e simular as revisões, de
modo que o ciclo completo possa ser mostrado em poucos cliques.

Repare que tudo passa pelos template methods (submeter_trabalho e
registrar_revisao), então as regras dos hotspots continuam valendo.
"""
from __future__ import annotations

import hashlib
import random

COMENTARIOS = {
    "alta": [
        "Contribuição clara e bem posicionada em relação aos trabalhos relacionados.",
        "A avaliação experimental é convincente e os resultados são relevantes.",
        "Texto bem escrito e organizado; recomendo a aceitação com ajustes menores.",
    ],
    "media": [
        "O tema é relevante, mas a avaliação poderia ser mais ampla.",
        "A metodologia é adequada, porém faltam comparações com abordagens existentes.",
        "Trabalho promissor; a discussão dos resultados precisa ser aprofundada.",
    ],
    "baixa": [
        "A contribuição não está clara frente aos trabalhos relacionados.",
        "A metodologia apresenta lacunas e os resultados não sustentam as conclusões.",
        "O texto precisa de revisão significativa de organização e clareza.",
    ],
}


def _gerador(*partes) -> random.Random:
    semente = int(hashlib.sha256(":".join(map(str, partes)).encode()).hexdigest()[:12], 16)
    return random.Random(semente)


def popular(aplicacao) -> dict:
    """Cadastra os revisores e submete os trabalhos de exemplo da aplicação."""
    evento = aplicacao.inicializar()
    dados = aplicacao.dados_de_exemplo()

    ja_cadastrados = {r["email"] for r in aplicacao.servicos.revisoes.listar_revisores(evento["id"])}
    novos_revisores = 0
    for revisor in dados.get("revisores", []):
        if revisor["email"] not in ja_cadastrados:
            aplicacao.servicos.revisoes.criar_revisor(evento["id"], revisor)
            novos_revisores += 1

    ja_submetidos = {s["titulo"] for s in aplicacao.servicos.submissoes.listar(evento["id"])}
    novas, recusadas = 0, []
    for sub in dados.get("submissoes", []):
        if sub["titulo"] in ja_submetidos:
            continue
        resultado = aplicacao.submeter_trabalho(sub)  # template method
        if resultado.aceita:
            novas += 1
        else:
            recusadas.append({"titulo": sub["titulo"], "erros": resultado.erros})
    return {"revisores": novos_revisores, "submissoes": novas, "recusadas": recusadas}


def simular_revisoes(aplicacao) -> int:
    """Preenche todas as revisões pendentes com notas coerentes com a 'qualidade' do exemplo."""
    evento = aplicacao.inicializar()
    qualidade = {s["titulo"]: s.get("qualidade", 0.6)
                 for s in aplicacao.dados_de_exemplo().get("submissoes", [])}
    submissoes = {s["id"]: s for s in aplicacao.servicos.submissoes.listar(evento["id"])}
    feitas = 0
    for aloc in aplicacao.servicos.revisoes.listar_alocacoes(evento_id=evento["id"], status="pendente"):
        sub = submissoes.get(aloc["submissao_id"])
        q = qualidade.get(sub["titulo"], 0.6) if sub else 0.6
        rng = _gerador(aloc["submissao_id"], aloc["revisor_id"])
        respostas = {}
        for c in aplicacao.formulario.criterios():
            amplitude = c.maximo - c.minimo
            valor = round(c.minimo + q * amplitude + rng.uniform(-0.2, 0.2) * amplitude)
            respostas[c.chave] = max(c.minimo, min(c.maximo, valor))
        faixa = "alta" if q >= 0.7 else "media" if q >= 0.45 else "baixa"
        comentario = " ".join(rng.sample(COMENTARIOS[faixa], 2))
        if aplicacao.registrar_revisao(aloc["id"], respostas, comentario).registrada:  # template method
            feitas += 1
    return feitas
