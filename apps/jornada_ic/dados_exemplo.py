"""
Dados fictícios de demonstração da JIC 2026.

'qualidade' (0 a 1) só é usada pelo simulador de revisões (scievent.demo).
"""

REVISORES = [
    {"nome": "André Siqueira", "email": "andre.siqueira@exemplo.edu.br", "instituicao": "Instituto de Computação",
     "areas": ["Inteligência Artificial"], "palavras_chave": ["aprendizado", "texto"]},
    {"nome": "Beatriz Cunha", "email": "beatriz.cunha@exemplo.edu.br", "instituicao": "Instituto de Computação",
     "areas": ["Sistemas e Redes"], "palavras_chave": ["redes", "sensores"]},
    {"nome": "Caio Medeiros", "email": "caio.medeiros@exemplo.edu.br", "instituicao": "Instituto de Computação",
     "areas": ["Computação Aplicada"], "palavras_chave": ["dados", "saúde"]},
    {"nome": "Denise Lacerda", "email": "denise.lacerda@exemplo.edu.br", "instituicao": "Instituto de Computação",
     "areas": ["Computação Aplicada", "Inteligência Artificial"], "palavras_chave": ["educação", "modelo"]},
]

SUBMISSOES = [
    {
        "titulo": "Aplicativo para acompanhamento de hidratação de idosos",
        "trilha": "Computação Aplicada", "palavras_chave": ["aplicativo", "saúde"],
        "autores": [{"nome": "Marina Lopes", "email": "marina.lopes@exemplo.edu.br", "instituicao": "Graduação"}],
        "resumo": ("Desenvolvemos um aplicativo que lembra idosos de beber água e envia um resumo diário "
                   "a familiares. Um piloto com 12 participantes durante quatro semanas mostrou aumento "
                   "no número de registros de ingestão."),
        "qualidade": 0.8,
    },
    {
        "titulo": "Monitoramento de umidade do solo com sensores de baixo custo",
        "trilha": "Sistemas e Redes", "palavras_chave": ["sensores", "redes"],
        "autores": [{"nome": "Pedro Albuquerque", "email": "pedro.albuquerque@exemplo.edu.br", "instituicao": "Graduação"}],
        "resumo": ("Montamos uma rede de sensores de umidade com microcontroladores de baixo custo para "
                   "uma horta comunitária. Os dados são enviados por rádio a um painel web. A rede "
                   "funcionou por 30 dias com duas trocas de bateria."),
        "qualidade": 0.7,
    },
    {
        "titulo": "Classificação de sentimentos em avaliações de disciplinas",
        "trilha": "Inteligência Artificial", "palavras_chave": ["texto", "classificação"],
        "autores": [{"nome": "Júlia Farias", "email": "julia.farias@exemplo.edu.br", "instituicao": "Graduação"}],
        "resumo": ("Treinamos um classificador de sentimentos com 3.000 comentários anônimos de "
                   "avaliações de disciplinas. O modelo atingiu 84% de acurácia e ajudou a coordenação "
                   "a identificar disciplinas com mais críticas."),
        "qualidade": 0.6,
    },
    {
        "titulo": "Painel de dados abertos sobre a merenda escolar do município",
        "trilha": "Computação Aplicada", "palavras_chave": ["dados", "educação"],
        "autores": [{"nome": "Rodrigo Bezerra", "email": "rodrigo.bezerra@exemplo.edu.br", "instituicao": "Graduação"}],
        "resumo": ("Reunimos dados públicos de compras da merenda escolar em um painel interativo que "
                   "mostra preços, fornecedores e entregas por escola. O painel revelou variações de "
                   "preço de até 35% para o mesmo item."),
        "qualidade": 0.75,
    },
    {
        "titulo": "Estudo inicial sobre segurança em redes domésticas",
        "trilha": "Sistemas e Redes", "palavras_chave": ["segurança", "redes"],
        "autores": [{"nome": "Thiago Nascimento", "email": "thiago.nascimento@exemplo.edu.br", "instituicao": "Graduação"}],
        "resumo": ("Levantamos as configurações padrão de roteadores domésticos e listamos riscos "
                   "comuns. O trabalho ainda não inclui testes práticos."),
        "qualidade": 0.35,
    },
    {
        "titulo": "Chatbot para dúvidas frequentes da secretaria do curso",
        "trilha": "Inteligência Artificial", "palavras_chave": ["texto", "modelo"],
        "autores": [{"nome": "Lívia Teixeira", "email": "livia.teixeira@exemplo.edu.br", "instituicao": "Graduação"}],
        "resumo": ("Criamos um chatbot que responde dúvidas frequentes sobre matrícula, estágio e "
                   "trancamento, com base no regimento do curso. Em testes com 40 perguntas, 33 "
                   "respostas foram consideradas corretas pela secretaria."),
        "qualidade": 0.9,
    },
]
