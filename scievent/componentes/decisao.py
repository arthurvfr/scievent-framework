"""Implementações do componente de Política de Decisão."""
from __future__ import annotations

from statistics import mean, pstdev

from scievent.interfaces import IPoliticaDecisao
from scievent.modelos import Decisao


class DecisaoPorMediaPonderada(IPoliticaDecisao):
    """
    Três faixas pela média das revisões (escala 1 a 5):
    acima do limiar oral -> apresentação oral; entre os limiares -> pôster;
    abaixo -> rejeitado. Sinaliza quando os revisores divergem muito.
    """

    def __init__(self, limiar_oral: float = 3.5, limiar_poster: float = 3.0,
                 limiar_divergencia: float = 1.0):
        self.limiar_oral = limiar_oral
        self.limiar_poster = limiar_poster
        self.limiar_divergencia = limiar_divergencia

    def descricao(self) -> str:
        return (f"Média >= {self.limiar_oral} vira oral, >= {self.limiar_poster} vira pôster, "
                f"abaixo disso é rejeitado; alerta de divergência acima de {self.limiar_divergencia}")

    def decidir(self, submissao, notas) -> Decisao:
        media = round(mean(notas), 2)
        desvio = round(pstdev(notas), 2) if len(notas) > 1 else 0.0
        if media >= self.limiar_oral:
            status, modalidade = "aceito", "oral"
        elif media >= self.limiar_poster:
            status, modalidade = "aceito", "poster"
        else:
            status, modalidade = "rejeitado", None
        justificativa = (f"Média {media:.2f} em {len(notas)} revisões (escala 1 a 5). "
                         f"Limiar oral {self.limiar_oral}, pôster {self.limiar_poster}.")
        if desvio > self.limiar_divergencia:
            justificativa += f" Atenção: revisores divergem (desvio {desvio:.2f})."
        return Decisao(status, modalidade, media, justificativa)


class DecisaoPorNotaMinima(IPoliticaDecisao):
    """Aceita para apresentação oral quem atinge a nota mínima; os demais são rejeitados."""

    def __init__(self, nota_minima: float = 6.0):
        self.nota_minima = nota_minima

    def descricao(self) -> str:
        return f"Aceita com nota >= {self.nota_minima}"

    def decidir(self, submissao, notas) -> Decisao:
        media = round(mean(notas), 2)
        if media >= self.nota_minima:
            return Decisao("aceito", "oral", media,
                           f"Nota {media:.2f} atinge o mínimo de {self.nota_minima}.")
        return Decisao("rejeitado", None, media,
                       f"Nota {media:.2f} abaixo do mínimo de {self.nota_minima}.")
