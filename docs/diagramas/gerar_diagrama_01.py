"""
Gera o diagrama de classes do framework com os componentes (Figura 1 do relatório).

Segue o formato da figura 12 do artigo "Framework para Pagamentos na Web":
a classe do framework guarda um atributo para cada componente, tipado pela
interface; setas tracejadas ligam o framework às interfaces; cada componente
realiza (implementa) a sua interface. Como na figura 14 do mesmo artigo, a
estrutura interna do framework e as aplicações aparecem em molduras separadas.

Uso:  python docs/diagramas/gerar_diagrama_01.py
Gera: docs/diagramas/01-framework-componentes.dot
      docs/img/diagrama-01-framework-componentes.png   (requer Graphviz)
"""
import html
import subprocess
from pathlib import Path

PASTA = Path(__file__).resolve().parent
DOT = PASTA / "01-framework-componentes.dot"
PNG = PASTA.parent / "img" / "diagrama-01-framework-componentes.png"

COR_BORDA = "#3730a3"
COR_TITULO = "#e8eaf9"
COR_INTERFACE = "#f3f4f6"
COR_APP = "#ecfdf5"
COR_BORDA_APP = "#0f766e"


def _linhas(itens, italico=False):
    if not itens:
        return " "
    partes = []
    for item in itens:
        texto = html.escape(item)
        partes.append(f"<I>{texto}</I>" if italico else texto)
    return '<BR ALIGN="LEFT"/>'.join(partes) + '<BR ALIGN="LEFT"/>'


def classe(nome, estereotipo=None, atributos=(), grupos=(), titulo_cor=COR_TITULO, borda=COR_BORDA,
           nome_italico=False):
    """grupos: [(rótulo do grupo ou None, [métodos], itálico?)]"""
    nome_html = f"<I>{html.escape(nome)}</I>" if nome_italico else html.escape(nome)
    cabecalho = (f'<FONT POINT-SIZE="10">«{html.escape(estereotipo)}»</FONT><BR/>' if estereotipo else "")
    linhas = [f'<TR><TD BGCOLOR="{titulo_cor}" CELLPADDING="6">{cabecalho}<B>{nome_html}</B></TD></TR>']
    linhas.append(f'<TR><TD ALIGN="LEFT" BALIGN="LEFT">{_linhas(atributos)}</TD></TR>')
    metodos = []
    for rotulo, itens, italico in grupos:
        if rotulo:
            metodos.append(f'<FONT POINT-SIZE="10" COLOR="#6b7280">{html.escape(rotulo)}</FONT><BR ALIGN="LEFT"/>')
        metodos.append(_linhas(itens, italico))
    linhas.append(f'<TR><TD ALIGN="LEFT" BALIGN="LEFT">{"".join(metodos) or " "}</TD></TR>')
    return (f'<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" COLOR="{borda}">'
            + "".join(linhas) + "</TABLE>>")


FRAMEWORK = classe(
    "FrameworkEventoCientifico", "abstract", nome_italico=True,
    atributos=[
        "+ ID_APLICACAO : str",
        "+ servicos : ServicosSciEvent",
        "+ validador : IValidadorSubmissao",
        "+ alocacao : IEstrategiaAlocacao",
        "+ formulario : IFormularioAvaliacao",
        "+ politica_decisao : IPoliticaDecisao",
        "+ gerador_programacao : IGeradorProgramacao",
        "+ canal_notificacao : ICanalNotificacao",
        "+ assistente : IAssistente",
    ],
    grupos=[
        ("construtor: cria os componentes chamando os hot-spots", [
            "+ FrameworkEventoCientifico(servicos)",
        ], False),
        ("métodos template (controle, @final)", [
            "+ inicializar() : dict",
            "+ submeter_trabalho(dados) : ResultadoSubmissao",
            "+ alocar_revisores() : list",
            "+ registrar_revisao(alocacao_id, respostas, comentario) : ResultadoRevisao",
            "+ consolidar_decisoes() : list",
            "+ gerar_programacao() : dict",
        ], False),
        ("hot-spots (métodos abstratos)", [
            "+ definir_evento() : dict",
            "+ criar_validador() : IValidadorSubmissao",
            "+ criar_estrategia_alocacao() : IEstrategiaAlocacao",
            "+ criar_formulario_avaliacao() : IFormularioAvaliacao",
            "+ criar_politica_decisao() : IPoliticaDecisao",
            "+ criar_gerador_programacao() : IGeradorProgramacao",
            "+ criar_canal_notificacao() : ICanalNotificacao",
        ], True),
        ("métodos hook (implementação padrão)", [
            "+ criar_assistente() : IAssistente",
            "+ ocultar_autores_na_revisao() : bool",
            "+ dados_de_exemplo() : dict",
        ], False),
    ],
)

# interface -> (métodos, [(componente, atributos, métodos, estereótipo)])
COMPONENTES = {
    "IValidadorSubmissao": (
        ["+ validar(submissao, evento) : list[str]"],
        [("ValidadorRigoroso", ["- min_palavras, max_palavras : int", "- min_kw, max_kw : int",
                                "- max_autores : int"], ["+ validar(submissao, evento) : list[str]"], None),
         ("ValidadorSimples", ["- max_palavras : int"], ["+ validar(submissao, evento) : list[str]"], None)],
    ),
    "IEstrategiaAlocacao": (
        ["+ alocar(submissoes, revisores, carga_atual) : list[dict]"],
        [("AlocacaoPorAfinidade", ["- n : int", "- evitar_mesma_instituicao : bool"],
          ["+ alocar(submissoes, revisores, carga_atual) : list[dict]"], None),
         ("AlocacaoRoundRobin", ["- n : int"], ["+ alocar(submissoes, revisores, carga_atual) : list[dict]"], None)],
    ),
    "IFormularioAvaliacao": (
        ["+ criterios() : list[Criterio]", "+ validar(respostas, comentario) : list[str]",
         "+ calcular_nota(respostas) : float"],
        [("FormularioPonderado", ["- _criterios : list[Criterio]", "- comentario_minimo : int"],
          ["+ criterios() : list[Criterio]", "+ validar(respostas, comentario) : list[str]",
           "+ calcular_nota(respostas) : float"], None),
         ("FormularioNotaUnica", ["- _criterio : Criterio", "- comentario_minimo : int"],
          ["+ criterios() : list[Criterio]", "+ validar(respostas, comentario) : list[str]",
           "+ calcular_nota(respostas) : float"], None)],
    ),
    "IPoliticaDecisao": (
        ["+ decidir(submissao, notas) : Decisao"],
        [("DecisaoPorMediaPonderada", ["- limiar_oral, limiar_poster : float", "- limiar_divergencia : float"],
          ["+ decidir(submissao, notas) : Decisao"], None),
         ("DecisaoPorNotaMinima", ["- nota_minima : float"], ["+ decidir(submissao, notas) : Decisao"], None)],
    ),
    "IGeradorProgramacao": (
        ["+ gerar(aceitos, evento, tentativa) : Programa", "+ verificar_conflitos(programa) : list[str]"],
        [("ProgramacaoPorTrilhas", ["- salas : list[str]", "- artigos_por_sessao : int",
                                    "- duracao, intervalo : int"],
          ["+ gerar(aceitos, evento, tentativa) : Programa", "+ verificar_conflitos(programa) : list[str]"], None),
         ("ProgramacaoSequencial", ["- sala : str", "- por_bloco : int", "- limite : str"],
          ["+ gerar(aceitos, evento, tentativa) : Programa", "+ verificar_conflitos(programa) : list[str]"], None)],
    ),
    "ICanalNotificacao": (
        ["+ canal : str", "+ formatar(tipo, contexto) : Mensagem"],
        [("NotificacaoEmail", ["- remetente : str", "+ canal = \"email\""],
          ["+ formatar(tipo, contexto) : Mensagem"], None),
         ("NotificacaoMural", ["+ canal = \"mural\""], ["+ formatar(tipo, contexto) : Mensagem"], None)],
    ),
    "IAssistente": (
        ["+ triar(submissao, evento) : dict", "+ meta_revisao(submissao, revisoes, decisao, evento) : str"],
        [("AssistenteAgentes", ["- cliente : ClienteAgentes"],
          ["+ triar(submissao, evento) : dict", "+ meta_revisao(submissao, revisoes, decisao, evento) : str"], None),
         ("SemAssistente", [], ["+ triar(submissao, evento) : None", "+ meta_revisao(...) : None"], "Null Object")],
    ),
}

APLICACOES = [
    ("CongressoNacional", ["+ ID_APLICACAO = \"congresso\""],
     [("implementa os hot-spots", ["+ definir_evento()", "+ criar_validador()", "+ criar_estrategia_alocacao()",
                                    "+ criar_formulario_avaliacao()", "+ criar_politica_decisao()",
                                    "+ criar_gerador_programacao()", "+ criar_canal_notificacao()"], False),
      ("redefine os hooks", ["+ criar_assistente()", "+ dados_de_exemplo()"], False)]),
    ("JornadaIniciacaoCientifica", ["+ ID_APLICACAO = \"jornada\""],
     [("implementa os hot-spots", ["+ definir_evento()", "+ criar_validador()", "+ criar_estrategia_alocacao()",
                                    "+ criar_formulario_avaliacao()", "+ criar_politica_decisao()",
                                    "+ criar_gerador_programacao()", "+ criar_canal_notificacao()"], False),
      ("redefine os hooks", ["+ ocultar_autores_na_revisao()", "+ dados_de_exemplo()"], False)]),
    ("Aplicação n", ["(ex.: WorkshopIA, seção 6.5)"],
     [("implementa os hot-spots", ["+ definir_evento()", "+ criar_...() para cada componente"], False)]),
]


def gerar_dot() -> str:
    linhas = [
        "digraph Framework {",
        '  graph [rankdir=LR, splines=true, nodesep=0.22, ranksep=0.9, fontname="Liberation Sans",'
        ' fontsize=15, newrank=true, pad=0.3, bgcolor="white"];',
        '  node  [shape=plaintext, fontname="Liberation Sans", fontsize=11];',
        '  edge  [color="#475569", penwidth=1.1, arrowsize=0.8];',
        "",
        "  subgraph cluster_apps {",
        '    label=<<B>Aplicações (parte variante)</B>>; labeljust=l; style="rounded,dashed";'
        f' color="{COR_BORDA_APP}"; margin=14;',
    ]
    for nome, atributos, grupos in APLICACOES:
        rotulo = classe(nome, None, atributos, grupos, titulo_cor=COR_APP, borda=COR_BORDA_APP)
        linhas.append(f'    "{nome}" [label={rotulo}];')
    linhas += [
        "  }",
        "",
        "  subgraph cluster_framework {",
        '    label=<<B>Estrutura interna do framework (parte invariante)</B>>; labeljust=l;'
        f' style=rounded; color="{COR_BORDA}"; margin=14;',
        f'    "FrameworkEventoCientifico" [label={FRAMEWORK}];',
    ]
    # Graphviz empilha a coluna de baixo para cima: declarar na ordem inversa
    # deixa as interfaces de cima para baixo na ordem do fluxo do evento.
    for interface, (metodos, comps) in reversed(list(COMPONENTES.items())):
        rotulo = classe(interface, "interface", [], [(None, metodos, True)], titulo_cor=COR_INTERFACE)
        linhas.append(f'    "{interface}" [label={rotulo}];')
        for nome, atributos, metodos_c, estereotipo in reversed(comps):
            linhas.append(f'    "{nome}" [label={classe(nome, estereotipo, atributos, [(None, metodos_c, False)])}];')
    linhas += ["  }", ""]

    for nome, _, _ in APLICACOES:
        estilo = ', style=dashed' if nome == "Aplicação n" else ""
        linhas.append(f'  "{nome}" -> "FrameworkEventoCientifico" [arrowhead=empty, arrowsize=1.2{estilo}];')
    for interface, (_, comps) in reversed(list(COMPONENTES.items())):
        linhas.append(f'  "FrameworkEventoCientifico" -> "{interface}" [style=dashed, arrowhead=vee];')
        for nome, *_ in reversed(comps):
            linhas.append(f'  "{interface}" -> "{nome}" [style=dashed, dir=back, arrowtail=empty, arrowsize=1.1];')
    linhas.append("}")
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    DOT.write_text(gerar_dot(), encoding="utf-8")
    subprocess.run(["dot", "-Tpng", "-Gdpi=170", str(DOT), "-o", str(PNG)], check=True)
    print(f"Gerado: {DOT.name} e {PNG.name}")
