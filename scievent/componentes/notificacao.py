"""Implementações do componente de Canal de Notificação."""
from __future__ import annotations

from scievent.interfaces import ICanalNotificacao
from scievent.modelos import Mensagem

_MODALIDADE = {"oral": "apresentação oral", "poster": "pôster", None: "-"}


class NotificacaoEmail(ICanalNotificacao):
    """E-mail formal assinado pela comissão (o envio é simulado pelo microsserviço)."""

    def __init__(self, remetente: str = "comissao@evento.example"):
        self.remetente = remetente

    @property
    def canal(self) -> str:
        return "email"

    def descricao(self) -> str:
        return f"E-mail formal enviado por {self.remetente}"

    def formatar(self, tipo: str, ctx: dict) -> Mensagem:
        sigla = ctx.get("evento", "")
        assinatura = f"\n\nAtenciosamente,\nComissão Organizadora do {sigla}\n{self.remetente}"
        if tipo == "submissao_recebida":
            return Mensagem(f"[{sigla}] Submissão #{ctx['id']} recebida",
                            f"Prezado(a) autor(a),\n\nConfirmamos o recebimento do trabalho "
                            f"\"{ctx['titulo']}\" (#{ctx['id']}). Ele seguirá para revisão por pares."
                            + assinatura)
        if tipo == "convite_revisao":
            return Mensagem(f"[{sigla}] Convite para revisão",
                            f"Prezado(a) {ctx['nome']},\n\nVocê foi designado(a) para revisar "
                            f"{ctx['quantidade']} trabalho(s). Acesse o sistema para avaliar." + assinatura)
        if tipo == "decisao":
            resultado = "ACEITO" if ctx["status"] == "aceito" else "NÃO ACEITO"
            extra = (f" na modalidade {_MODALIDADE.get(ctx.get('modalidade'))}"
                     if ctx["status"] == "aceito" else "")
            return Mensagem(f"[{sigla}] Resultado da avaliação: {resultado}",
                            f"Prezado(a) autor(a),\n\nO trabalho \"{ctx['titulo']}\" foi {resultado}"
                            f"{extra}, com nota média {ctx['media']:.2f}." + assinatura)
        if tipo == "programacao_publicada":
            return Mensagem(f"[{sigla}] Programação publicada",
                            f"Prezados(as),\n\nA programação do evento está disponível, com "
                            f"{ctx['sessoes']} sessões." + assinatura)
        return Mensagem(f"[{sigla}] {tipo}", str(ctx))


class NotificacaoMural(ICanalNotificacao):
    """Recado curto publicado no mural do evento (sem e-mail)."""

    @property
    def canal(self) -> str:
        return "mural"

    def descricao(self) -> str:
        return "Recados curtos no mural do evento"

    def formatar(self, tipo: str, ctx: dict) -> Mensagem:
        if tipo == "submissao_recebida":
            return Mensagem("Trabalho recebido", f"\"{ctx['titulo']}\" entrou na fila de avaliação.")
        if tipo == "convite_revisao":
            return Mensagem("Nova avaliação", f"{ctx['nome']}, há {ctx['quantidade']} trabalho(s) para você avaliar.")
        if tipo == "decisao":
            if ctx["status"] == "aceito":
                return Mensagem("Trabalho aprovado", f"\"{ctx['titulo']}\" foi aprovado (nota {ctx['media']:.1f}).")
            return Mensagem("Resultado", f"\"{ctx['titulo']}\" não atingiu a nota mínima ({ctx['media']:.1f}).")
        if tipo == "programacao_publicada":
            return Mensagem("Programação no ar", f"Confira as {ctx['sessoes']} sessões da jornada.")
        return Mensagem(tipo, str(ctx))
