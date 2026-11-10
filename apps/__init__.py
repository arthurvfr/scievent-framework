"""
Catálogo das aplicações construídas com o framework SciEvent.

Para disponibilizar uma nova aplicação na interface web, importe a classe
aqui e acrescente-a à tupla abaixo (ver "Como criar uma nova aplicação" no README).
"""
from apps.congresso_nacional.aplicacao import CongressoNacional
from apps.jornada_ic.aplicacao import JornadaIniciacaoCientifica

APLICACOES = {cls.ID_APLICACAO: cls for cls in (CongressoNacional, JornadaIniciacaoCientifica)}
