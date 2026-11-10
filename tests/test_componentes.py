"""Testes unitários dos componentes (cada um isolado, sem microsserviços)."""
from scievent.componentes import (
    AlocacaoPorAfinidade, AlocacaoRoundRobin, DecisaoPorMediaPonderada, DecisaoPorNotaMinima,
    FormularioNotaUnica, FormularioPonderado, NotificacaoEmail, NotificacaoMural,
    ProgramacaoPorTrilhas, ProgramacaoSequencial, ValidadorRigoroso, ValidadorSimples,
)

EVENTO = {"sigla": "TESTE", "trilhas": [{"nome": "IA", "palavras_chave": ["redes neurais"]},
                                        {"nome": "ES", "palavras_chave": ["reuso"]}]}
AUTOR = {"nome": "Ana Souza", "email": "ana@x.br", "instituicao": "UFX"}


def submissao(**extra):
    base = {"titulo": "Um título suficientemente longo", "resumo": "palavra " * 80,
            "palavras_chave": ["a", "b", "c"], "trilha": "IA", "autores": [AUTOR]}
    return {**base, **extra}


def test_validador_rigoroso_aceita_submissao_correta():
    assert ValidadorRigoroso().validar(submissao(), EVENTO) == []


def test_validador_rigoroso_aponta_resumo_curto_e_anonimato():
    erros = ValidadorRigoroso().validar(submissao(resumo="Trabalho de Ana Souza."), EVENTO)
    assert any("resumo tem" in e for e in erros)
    assert any("Anonimato" in e for e in erros)


def test_validador_simples_e_mais_permissivo():
    sub = submissao(palavras_chave=[], trilha="")
    assert ValidadorSimples().validar(sub, EVENTO) == []
    assert ValidadorRigoroso().validar(sub, EVENTO) != []


def test_alocacao_por_afinidade_evita_conflito_e_respeita_quantidade():
    revisores = [
        {"id": 1, "email": "r1@x.br", "instituicao": "UFX", "areas": ["IA"], "palavras_chave": []},
        {"id": 2, "email": "r2@x.br", "instituicao": "UFY", "areas": ["IA"], "palavras_chave": []},
        {"id": 3, "email": "r3@x.br", "instituicao": "UFZ", "areas": ["ES"], "palavras_chave": []},
    ]
    pares = AlocacaoPorAfinidade(revisores_por_trabalho=2).alocar([{**submissao(), "id": 10}], revisores)
    escolhidos = [p["revisor_id"] for p in pares]
    assert 1 not in escolhidos          # mesma instituição do autor
    assert escolhidos[0] == 2           # maior afinidade primeiro
    assert len(escolhidos) == 2


def test_round_robin_distribui_em_rodizio():
    revisores = [{"id": i, "email": f"r{i}@x.br"} for i in (1, 2)]
    subs = [{**submissao(), "id": i} for i in (10, 11, 12, 13)]
    pares = AlocacaoRoundRobin().alocar(subs, revisores)
    assert [p["revisor_id"] for p in pares] == [1, 2, 1, 2]


def test_formulario_ponderado_calcula_media_ponderada():
    f = FormularioPonderado()
    respostas = {"originalidade": 5, "relevancia": 3, "metodologia": 4, "clareza": 2}
    assert f.validar(respostas, "x" * 40) == []
    assert f.calcular_nota(respostas) == 3.7  # 0.3*5 + 0.2*3 + 0.3*4 + 0.2*2


def test_formulario_nota_unica_valida_escala():
    f = FormularioNotaUnica()
    assert f.validar({"nota": 11}, "") != []
    assert f.calcular_nota({"nota": 7}) == 7.0


def test_politicas_de_decisao():
    d = DecisaoPorMediaPonderada()
    assert (d.decidir({}, [4, 4, 3]).status, d.decidir({}, [4, 4, 3]).modalidade) == ("aceito", "oral")
    assert d.decidir({}, [3, 3, 3.2]).modalidade == "poster"
    assert d.decidir({}, [2, 2, 3]).status == "rejeitado"
    assert "divergem" in d.decidir({}, [1, 5, 4]).justificativa
    assert DecisaoPorNotaMinima(6).decidir({}, [5.5]).status == "rejeitado"


def _aceito(i, trilha, email):
    return {"id": i, "titulo": f"T{i}", "trilha": trilha, "decisao": {"modalidade": "oral"},
            "autores": [{"nome": email, "email": email}]}


def test_programacao_por_trilhas_detecta_autor_em_duas_salas():
    aceitos = [_aceito(1, "IA", "x@x"), _aceito(2, "ES", "x@x")]
    gerador = ProgramacaoPorTrilhas(salas=("A", "B"))
    programa = gerador.gerar(aceitos, EVENTO, tentativa=1)
    assert len(programa.sessoes) == 2
    assert gerador.verificar_conflitos(programa)  # mesmo autor, mesmo horário


def test_programacao_sequencial_respeita_horario_limite():
    aceitos = [_aceito(i, "IA", f"{i}@x") for i in range(30)]
    gerador = ProgramacaoSequencial(horario_limite="15:00")
    assert gerador.verificar_conflitos(gerador.gerar(aceitos, EVENTO, 1))


def test_canais_de_notificacao_formatam_cada_tipo():
    ctx = {"evento": "T", "titulo": "X", "id": 1, "nome": "R", "quantidade": 2,
           "status": "aceito", "modalidade": "oral", "media": 4.0, "sessoes": 3}
    for canal in (NotificacaoEmail(), NotificacaoMural()):
        for tipo in ("submissao_recebida", "convite_revisao", "decisao", "programacao_publicada"):
            msg = canal.formatar(tipo, ctx)
            assert msg.assunto and msg.corpo
