"""
SciEvent — Framework para Sistemas de Gerenciamento de Eventos Científicos
usando Microsserviços e Componentes de Software (e Agentes de IA, opcional).

Pacotes:
    scievent.framework    núcleo (classe com os template methods e hotspots)
    scievent.interfaces   contratos dos componentes plugáveis
    scievent.componentes  implementações prontas dos componentes
    scievent.clientes     clientes HTTP dos microsserviços
    scievent.chassi       base comum dos microsserviços (Flask + SQLite + registro)
"""

__version__ = "1.0.0"
