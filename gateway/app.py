"""
API GATEWAY + Interface Web do SciEvent — porta 5000.

Ponto único de entrada do sistema. Tem dois papéis:

1) API Gateway (rotas /api/...): repassa a requisição ao microsserviço
   certo, descobrindo o endereço no Service Registry. O cliente externo
   só conhece a porta 5000.

       GET|POST|PUT|PATCH|DELETE  /api/<servico>/<caminho>
       GET                        /api                  (lista as rotas)
       GET                        /health

   Exemplos:
       GET  /api/registro/servicos
       GET  /api/submissoes/submissoes?evento_id=1
       GET  /api/agentes/papeis

2) Interface web (rotas /a/<aplicacao>/...): cada aplicação construída com o
   framework ganha suas telas. As telas chamam os TEMPLATE METHODS da
   aplicação, e o rodapé de cada página mostra quais microsserviços foram
   usados para montá-la.
"""
from __future__ import annotations

import os
import sys
import time
from collections import Counter, defaultdict
from functools import wraps

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests  # noqa: E402
from flask import (Flask, Response, abort, flash, g, has_request_context, jsonify,  # noqa: E402
                   redirect, render_template, request, url_for)

from apps import APLICACOES  # noqa: E402
from scievent import __version__, config, demo  # noqa: E402
from scievent.chassi import iniciar  # noqa: E402
from scievent.clientes import ErroServico, ResolvedorServicos, observar_chamadas  # noqa: E402
from scievent.componentes import SemAssistente  # noqa: E402

app = Flask(__name__)
app.secret_key = os.environ.get("SCIEVENT_SEGREDO", "scievent-desenvolvimento")
app.config["SCIEVENT_NOME"] = "gateway"
app.config["SCIEVENT_DESCRICAO"] = "API Gateway e interface web"
app.json.ensure_ascii = False

resolvedor = ResolvedorServicos()
_instancias: dict = {}

SERVICOS_ROTEAVEIS = [n for n in config.PORTAS if n != "gateway"]

ETAPAS = [
    ("painel", "Visão geral"),
    ("submeter", "Submeter trabalho"),
    ("trabalhos", "Trabalhos"),
    ("revisores", "Revisores e alocação"),
    ("revisoes", "Revisões"),
    ("decisoes", "Decisões"),
    ("programacao", "Programação"),
    ("notificacoes", "Notificações"),
    ("assistente", "Assistente de IA"),
]


# ---------------------------------------------------------------------------
# Rastreamento dos microsserviços usados em cada tela
# ---------------------------------------------------------------------------

def _anotar_servico(nome: str) -> None:
    if has_request_context():
        g.setdefault("servicos_usados", [])
        if nome not in g.servicos_usados:
            g.servicos_usados.append(nome)


observar_chamadas(_anotar_servico)


@app.context_processor
def contexto_global():
    usados = g.get("servicos_usados", [])
    return {
        "servicos_da_tela": [{"nome": n, "porta": config.porta(n)} for n in usados],
        "aplicacoes": APLICACOES,
        "etapas": ETAPAS,
        "versao": __version__,
    }


def _resumo_servicos() -> str:
    usados = g.get("servicos_usados", [])
    return ", ".join(f"{n}:{config.porta(n)}" for n in usados) or "nenhum"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def obter_aplicacao(app_id: str):
    """Instância (única) da aplicação construída com o framework."""
    if app_id not in APLICACOES:
        abort(404)
    if app_id not in _instancias:
        _instancias[app_id] = APLICACOES[app_id]()
    return _instancias[app_id]


def acao(funcao):
    """Decorador das ações (POST): mostra o resultado e os serviços usados, e volta à tela."""
    @wraps(funcao)
    def envoltorio(app_id, *args, **kwargs):
        destino, mensagem = funcao(obter_aplicacao(app_id), *args, **kwargs)
        flash(f"{mensagem}  ·  Microsserviços usados: {_resumo_servicos()}", "sucesso")
        return redirect(url_for(destino, app_id=app_id))
    return envoltorio


@app.errorhandler(ErroServico)
def servico_indisponivel(erro: ErroServico):
    return render_template("erro.html", erro=erro), 503


@app.template_filter("status")
def rotulo_status(status):
    return {"submetida": "Submetida", "em_revisao": "Em revisão", "aceito": "Aceito",
            "rejeitado": "Rejeitado", "pendente": "Pendente", "concluida": "Concluída"}.get(status, status)


@app.template_filter("modalidade")
def rotulo_modalidade(modalidade):
    return {"oral": "Apresentação oral", "poster": "Pôster"}.get(modalidade, "")


# ---------------------------------------------------------------------------
# 1) API GATEWAY
# ---------------------------------------------------------------------------

@app.get("/health")
def saude():
    return jsonify({"servico": "gateway", "status": "ok"})


@app.get("/api")
def indice_api():
    return jsonify({
        "gateway": f"http://{config.HOST}:{config.porta('gateway')}",
        "uso": "/api/<servico>/<caminho>  (o gateway repassa ao microsserviço)",
        "servicos": {n: f"/api/{n}/" for n in SERVICOS_ROTEAVEIS},
    })


@app.route("/api/<servico>/", defaults={"caminho": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.route("/api/<servico>/<path:caminho>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def proxy(servico, caminho):
    """Roteamento: /api/<servico>/<caminho> -> http://<host do servico>/<caminho>."""
    if servico not in SERVICOS_ROTEAVEIS:
        return jsonify({"erro": f"Serviço desconhecido: {servico}"}), 404
    destino = f"{resolvedor.url(servico)}/{caminho}"
    try:
        resposta = requests.request(request.method, destino, params=request.args,
                                    json=request.get_json(silent=True), timeout=config.TIMEOUT_HTTP)
    except requests.RequestException:
        return jsonify({"erro": f"Microsserviço '{servico}' indisponível em {destino}"}), 503
    return Response(resposta.content, status=resposta.status_code,
                    content_type=resposta.headers.get("Content-Type", "application/json"))


# ---------------------------------------------------------------------------
# 2) INTERFACE WEB — páginas gerais
# ---------------------------------------------------------------------------

@app.get("/")
def inicio():
    for app_id in APLICACOES:
        obter_aplicacao(app_id).inicializar()   # cria o evento na primeira visita
    qualquer = obter_aplicacao(next(iter(APLICACOES)))
    eventos = {e["aplicacao"]: e for e in qualquer.servicos.eventos.listar()}
    cards = [{"id": app_id, "classe": cls.__name__, "evento": eventos[app_id]}
             for app_id, cls in APLICACOES.items() if app_id in eventos]
    try:
        servicos = resolvedor_listar()
    except ErroServico:
        servicos = []
    return render_template("inicio.html", cards=cards, servicos=servicos)


def _rotas_do_gateway() -> list[str]:
    return sorted({f"{m} {r.rule}" for r in app.url_map.iter_rules() if r.endpoint != "static"
                   for m in r.methods - {"HEAD", "OPTIONS"}})


def resolvedor_listar() -> list[dict]:
    _anotar_servico("registro")
    try:
        return requests.get(f"{resolvedor.url('registro')}/servicos", timeout=2).json()
    except requests.RequestException:
        raise ErroServico("registro", "o Service Registry não respondeu")


@app.get("/microservicos")
def microservicos():
    """Tela exigida no relatório: microsserviços em execução e suas portas."""
    linhas = []
    for s in resolvedor_listar():
        inicio_ping = time.perf_counter()
        try:
            responde = requests.get(f"{s['url']}/health", timeout=2).status_code == 200
            latencia = round((time.perf_counter() - inicio_ping) * 1000, 1)
        except requests.RequestException:
            responde, latencia = False, None
        if s["nome"] == "gateway":
            endpoints = _rotas_do_gateway()
        else:
            try:
                endpoints = requests.get(f"{s['url']}/", timeout=2).json().get("endpoints", [])
            except (requests.RequestException, ValueError):
                endpoints = []
        linhas.append({**s, "latencia_ms": latencia, "endpoints": endpoints, "responde": responde})
    esperados = set(config.PORTAS)
    ausentes = sorted(esperados - {s["nome"] for s in linhas})
    return render_template("microservicos.html", linhas=linhas, ausentes=ausentes)


# ---------------------------------------------------------------------------
# 2) INTERFACE WEB — telas de cada aplicação
# ---------------------------------------------------------------------------

@app.get("/a/<app_id>/")
def painel(app_id):
    aplicacao = obter_aplicacao(app_id)
    s = aplicacao.servicos
    evento = s.eventos.obter(aplicacao.inicializar()["id"])   # dados atuais do microsserviço
    submissoes = s.submissoes.listar(evento["id"])
    alocacoes = s.revisoes.listar_alocacoes(evento_id=evento["id"])
    metricas = {
        "submissoes": len(submissoes),
        "por_status": Counter(x["status"] for x in submissoes),
        "revisores": len(s.revisoes.listar_revisores(evento["id"])),
        "alocacoes": len(alocacoes),
        "revisoes_pendentes": sum(1 for a in alocacoes if a["status"] == "pendente"),
        "notificacoes": len(s.notificacoes.listar(evento["id"])),
        "programacao": s.programacao.obter(evento["id"]) is not None,
    }
    return render_template("painel.html", aplicacao=aplicacao, app_id=app_id, evento=evento,
                           m=metricas, pagina="painel")


@app.post("/a/<app_id>/popular")
@acao
def popular(aplicacao):
    r = demo.popular(aplicacao)
    return "painel", f"Dados de exemplo carregados: {r['revisores']} revisores e {r['submissoes']} submissões."


@app.post("/a/<app_id>/ciclo-completo")
@acao
def ciclo_completo(aplicacao):
    alocacoes = aplicacao.alocar_revisores()
    revisoes = demo.simular_revisoes(aplicacao)
    decisoes = aplicacao.consolidar_decisoes()
    programa = aplicacao.gerar_programacao()
    return "painel", (f"Ciclo executado: {len(alocacoes)} alocações, {revisoes} revisões simuladas, "
                      f"{len(decisoes)} decisões e programação com {len(programa['sessoes'])} sessões.")


@app.route("/a/<app_id>/submeter", methods=["GET", "POST"])
def submeter(app_id):
    aplicacao = obter_aplicacao(app_id)
    evento = aplicacao.inicializar()
    erros, valores = [], {}
    if request.method == "POST":
        f = request.form
        valores = f.to_dict()
        autores = [{"nome": f.get(f"autor_nome_{i}", ""), "email": f.get(f"autor_email_{i}", ""),
                    "instituicao": f.get(f"autor_inst_{i}", "")} for i in range(3)]
        resultado = aplicacao.submeter_trabalho({          # TEMPLATE METHOD
            "titulo": f.get("titulo"), "resumo": f.get("resumo"),
            "palavras_chave": f.get("palavras_chave", ""), "trilha": f.get("trilha"),
            "autores": autores,
        })
        if resultado.aceita:
            flash(f"Submissão #{resultado.submissao['id']} recebida.  ·  "
                  f"Microsserviços usados: {_resumo_servicos()}", "sucesso")
            return redirect(url_for("trabalhos", app_id=app_id))
        erros = resultado.erros
    return render_template("submeter.html", aplicacao=aplicacao, app_id=app_id, evento=evento,
                           erros=erros, v=valores, pagina="submeter")


@app.get("/a/<app_id>/trabalhos")
def trabalhos(app_id):
    aplicacao = obter_aplicacao(app_id)
    evento = aplicacao.inicializar()
    submissoes = aplicacao.servicos.submissoes.listar(evento["id"])
    return render_template("trabalhos.html", aplicacao=aplicacao, app_id=app_id, evento=evento,
                           submissoes=submissoes, pagina="trabalhos")


@app.get("/a/<app_id>/revisores")
def revisores(app_id):
    aplicacao = obter_aplicacao(app_id)
    evento = aplicacao.inicializar()
    s = aplicacao.servicos
    lista = s.revisoes.listar_revisores(evento["id"])
    alocacoes = s.revisoes.listar_alocacoes(evento_id=evento["id"])
    carga = Counter(a["revisor_id"] for a in alocacoes)
    submissoes = {x["id"]: x for x in s.submissoes.listar(evento["id"])}
    por_submissao = defaultdict(list)
    for a in alocacoes:
        por_submissao[a["submissao_id"]].append(a)
    aguardando = sum(1 for x in submissoes.values() if x["status"] == "submetida")
    return render_template("revisores.html", aplicacao=aplicacao, app_id=app_id, evento=evento,
                           revisores=lista, carga=carga, por_submissao=por_submissao,
                           submissoes=submissoes, aguardando=aguardando, pagina="revisores")


@app.post("/a/<app_id>/revisores")
@acao
def cadastrar_revisor(aplicacao):
    f = request.form
    dividir = lambda texto: [p.strip() for p in (texto or "").split(",") if p.strip()]  # noqa: E731
    aplicacao.servicos.revisoes.criar_revisor(aplicacao.inicializar()["id"], {
        "nome": f.get("nome"), "email": f.get("email"), "instituicao": f.get("instituicao"),
        "areas": f.getlist("areas"), "palavras_chave": dividir(f.get("palavras_chave")),
    })
    return "revisores", f"Revisor {f.get('nome')} cadastrado."


@app.post("/a/<app_id>/alocar")
@acao
def alocar(aplicacao):
    alocacoes = aplicacao.alocar_revisores()                 # TEMPLATE METHOD
    return "revisores", f"{len(alocacoes)} alocações criadas por {aplicacao.alocacao.nome}."


@app.get("/a/<app_id>/revisoes")
def revisoes(app_id):
    aplicacao = obter_aplicacao(app_id)
    evento = aplicacao.inicializar()
    s = aplicacao.servicos
    submissoes = {x["id"]: x for x in s.submissoes.listar(evento["id"])}
    pendentes = s.revisoes.listar_alocacoes(evento_id=evento["id"], status="pendente")
    feitas = s.revisoes.listar_revisoes(evento_id=evento["id"])
    return render_template("revisoes.html", aplicacao=aplicacao, app_id=app_id, evento=evento,
                           submissoes=submissoes, pendentes=pendentes, feitas=feitas,
                           criterios=aplicacao.formulario.criterios(),
                           ocultar=aplicacao.ocultar_autores_na_revisao(), pagina="revisoes")


@app.post("/a/<app_id>/revisoes/<int:alocacao_id>")
def registrar_revisao(app_id, alocacao_id):
    aplicacao = obter_aplicacao(app_id)
    respostas = {c.chave: request.form.get(c.chave) for c in aplicacao.formulario.criterios()}
    resultado = aplicacao.registrar_revisao(alocacao_id, respostas, request.form.get("comentario", ""))
    if resultado.registrada:
        flash(f"Revisão registrada com nota {resultado.revisao['nota']:.2f}.  ·  "
              f"Microsserviços usados: {_resumo_servicos()}", "sucesso")
    else:
        flash("Revisão não registrada: " + " ".join(resultado.erros), "erro")
    return redirect(url_for("revisoes", app_id=app_id))


@app.post("/a/<app_id>/simular-revisoes")
@acao
def simular(aplicacao):
    return "revisoes", f"{demo.simular_revisoes(aplicacao)} revisões simuladas (demonstração)."


@app.get("/a/<app_id>/decisoes")
def decisoes(app_id):
    aplicacao = obter_aplicacao(app_id)
    evento = aplicacao.inicializar()
    s = aplicacao.servicos
    submissoes = s.submissoes.listar(evento["id"])
    revisoes_por_sub = Counter(r["submissao_id"] for r in s.revisoes.listar_revisoes(evento_id=evento["id"]))
    return render_template("decisoes.html", aplicacao=aplicacao, app_id=app_id, evento=evento,
                           submissoes=submissoes, revisoes_por_sub=revisoes_por_sub, pagina="decisoes")


@app.post("/a/<app_id>/consolidar")
@acao
def consolidar(aplicacao):
    decididas = aplicacao.consolidar_decisoes()             # TEMPLATE METHOD
    aceitas = sum(1 for d in decididas if d["status"] == "aceito")
    return "decisoes", f"{len(decididas)} trabalhos decididos ({aceitas} aceitos) por {aplicacao.politica_decisao.nome}."


@app.get("/a/<app_id>/programacao")
def programacao(app_id):
    aplicacao = obter_aplicacao(app_id)
    evento = aplicacao.inicializar()
    programa = aplicacao.servicos.programacao.obter(evento["id"])
    grade, salas = [], []
    if programa:
        salas = list(dict.fromkeys(sessao["sala"] for sessao in programa["sessoes"]))
        por_horario = defaultdict(dict)
        for sessao in programa["sessoes"]:
            por_horario[(sessao["inicio"], sessao["fim"])][sessao["sala"]] = sessao
        grade = sorted(por_horario.items())
    aceitos = len(aplicacao.servicos.submissoes.listar(evento["id"], status="aceito"))
    return render_template("programacao.html", aplicacao=aplicacao, app_id=app_id, evento=evento,
                           programa=programa, grade=grade, salas=salas, aceitos=aceitos,
                           pagina="programacao")


@app.post("/a/<app_id>/gerar-programacao")
@acao
def gerar_programacao(aplicacao):
    programa = aplicacao.gerar_programacao()                # TEMPLATE METHOD
    return "programacao", (f"Programação gerada em {len(programa['tentativas'])} tentativa(s), "
                           f"{len(programa['sessoes'])} sessões.")


@app.get("/a/<app_id>/notificacoes")
def notificacoes(app_id):
    aplicacao = obter_aplicacao(app_id)
    evento = aplicacao.inicializar()
    lista = aplicacao.servicos.notificacoes.listar(evento["id"])
    return render_template("notificacoes.html", aplicacao=aplicacao, app_id=app_id, evento=evento,
                           notificacoes=lista, pagina="notificacoes")


@app.get("/a/<app_id>/assistente")
def assistente(app_id):
    aplicacao = obter_aplicacao(app_id)
    evento = aplicacao.inicializar()
    usa_ia = not isinstance(aplicacao.assistente, SemAssistente)
    papeis, mensagens, modelo = [], [], None
    if usa_ia:
        papeis = aplicacao.servicos.agentes.papeis()
        modelo = aplicacao.servicos.agentes.modelo()
        mensagens = aplicacao.servicos.agentes.pool(evento["id"])
    return render_template("assistente.html", aplicacao=aplicacao, app_id=app_id, evento=evento,
                           usa_ia=usa_ia, papeis=papeis, mensagens=mensagens, modelo=modelo,
                           pagina="assistente")


if __name__ == "__main__":
    iniciar(app)
