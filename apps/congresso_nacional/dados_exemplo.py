"""
Dados fictícios de demonstração do CBCA 2026.

'qualidade' (0 a 1) só é usada pelo simulador de revisões (scievent.demo):
indica se o trabalho tende a receber notas altas ou baixas.
"""

REVISORES = [
    {"nome": "Carla Mendes", "email": "carla.mendes@exemplo.edu.br", "instituicao": "UFPE",
     "areas": ["Inteligência Artificial"],
     "palavras_chave": ["aprendizado de máquina", "redes neurais", "visão computacional"]},
    {"nome": "Rafael Lima", "email": "rafael.lima@exemplo.edu.br", "instituicao": "UFCG",
     "areas": ["Engenharia de Software"], "palavras_chave": ["microsserviços", "arquitetura", "testes"]},
    {"nome": "Juliana Rocha", "email": "juliana.rocha@exemplo.edu.br", "instituicao": "USP",
     "areas": ["Inteligência Artificial", "Computação Aplicada à Educação"],
     "palavras_chave": ["modelos de linguagem", "feedback", "avaliação automática"]},
    {"nome": "Marcos Tavares", "email": "marcos.tavares@exemplo.edu.br", "instituicao": "UFMG",
     "areas": ["Sistemas Distribuídos"], "palavras_chave": ["nuvem", "escalabilidade", "contêineres"]},
    {"nome": "Patrícia Nunes", "email": "patricia.nunes@exemplo.edu.br", "instituicao": "UNICAMP",
     "areas": ["Engenharia de Software", "Computação Aplicada à Educação"],
     "palavras_chave": ["reuso", "frameworks", "ensino"]},
    {"nome": "Eduardo Santos", "email": "eduardo.santos@exemplo.edu.br", "instituicao": "UFBA",
     "areas": ["Sistemas Distribuídos", "Inteligência Artificial"],
     "palavras_chave": ["borda", "latência", "aprendizado de máquina"]},
    {"nome": "Fernanda Alves", "email": "fernanda.alves@exemplo.edu.br", "instituicao": "UFRN",
     "areas": ["Computação Aplicada à Educação"],
     "palavras_chave": ["ambiente virtual", "estudantes", "aprendizagem"]},
    {"nome": "Lucas Barbosa", "email": "lucas.barbosa@exemplo.edu.br", "instituicao": "UFAL",
     "areas": ["Inteligência Artificial", "Engenharia de Software"],
     "palavras_chave": ["agentes", "modelos de linguagem", "componentes"]},
]

SUBMISSOES = [
    {
        "titulo": "Agentes baseados em modelos de linguagem para triagem de chamados acadêmicos",
        "trilha": "Inteligência Artificial",
        "palavras_chave": ["modelos de linguagem", "agentes", "classificação"],
        "autores": [{"nome": "Helena Prado", "email": "helena.prado@exemplo.edu.br", "instituicao": "UFPI"},
                    {"nome": "Tiago Moura", "email": "tiago.moura@exemplo.edu.br", "instituicao": "UFPI"}],
        "resumo": ("Secretarias acadêmicas recebem milhares de chamados por semestre, muitos deles "
                   "repetitivos. Este trabalho propõe um sistema de agentes baseados em modelos de "
                   "linguagem que classifica cada chamado, consulta a base de normas da instituição e "
                   "redige uma resposta inicial para revisão humana. Os agentes trocam mensagens "
                   "estruturadas, o que reduz respostas inconsistentes. Em uma avaliação com 1.200 "
                   "chamados reais anonimizados, o sistema classificou corretamente 91% dos casos e "
                   "reduziu em 40% o tempo médio de atendimento, sem aumento de reclamações."),
        "qualidade": 0.85,
    },
    {
        "titulo": "Arquitetura de microsserviços para sistemas acadêmicos: um estudo de caso de reuso",
        "trilha": "Engenharia de Software",
        "palavras_chave": ["microsserviços", "reuso", "arquitetura"],
        "autores": [{"nome": "Helena Prado", "email": "helena.prado@exemplo.edu.br", "instituicao": "UFPI"},
                    {"nome": "Bianca Freitas", "email": "bianca.freitas@exemplo.edu.br", "instituicao": "IFAL"}],
        "resumo": ("Sistemas acadêmicos costumam nascer como monólitos difíceis de evoluir. Relatamos a "
                   "migração de um sistema de matrículas para uma arquitetura de microsserviços, com "
                   "foco no reuso de componentes entre três campi. Descrevemos a decomposição por "
                   "subdomínio, o uso de um gateway de API e de um registro de serviços, e as métricas "
                   "de reuso coletadas. Os resultados mostram que 68% do código passou a ser "
                   "compartilhado e que o tempo de entrega de novas funcionalidades caiu pela metade."),
        "qualidade": 0.8,
    },
    {
        "titulo": "Detecção de pessoas em vídeos de vigilância com redes convolucionais leves",
        "trilha": "Inteligência Artificial",
        "palavras_chave": ["visão computacional", "redes neurais", "aprendizado de máquina"],
        "autores": [{"nome": "Diego Cardoso", "email": "diego.cardoso@exemplo.edu.br", "instituicao": "UFAL"}],
        "resumo": ("Câmeras de vigilância geram horas de vídeo que raramente são analisadas. Avaliamos "
                   "redes convolucionais leves para detectar pessoas em vídeos de baixa resolução, "
                   "executando em computadores sem placa de vídeo. Comparamos quatro arquiteturas em "
                   "um conjunto de 3.000 quadros anotados de ambientes internos. A melhor configuração "
                   "obteve precisão de 0,87 a 14 quadros por segundo, o que indica viabilidade para "
                   "monitoramento em tempo quase real em órgãos com pouca infraestrutura."),
        "qualidade": 0.7,
    },
    {
        "titulo": "Orquestração de contêineres em nuvem híbrida com tolerância a falhas",
        "trilha": "Sistemas Distribuídos",
        "palavras_chave": ["contêineres", "nuvem", "tolerância a falhas"],
        "autores": [{"nome": "Renata Gomes", "email": "renata.gomes@exemplo.edu.br", "instituicao": "UFPB"}],
        "resumo": ("Ambientes de nuvem híbrida combinam servidores locais e provedores públicos, mas "
                   "falhas na conexão entre eles derrubam serviços críticos. Propomos uma política de "
                   "orquestração de contêineres que replica serviços de forma adaptativa conforme a "
                   "latência e a disponibilidade de cada lado. Experimentos com injeção de falhas em "
                   "um cluster de 24 nós mostraram disponibilidade de 99,95% e redução de 30% no "
                   "custo em relação à replicação estática."),
        "qualidade": 0.75,
    },
    {
        "titulo": "Feedback automático em exercícios de programação com modelos de linguagem",
        "trilha": "Computação Aplicada à Educação",
        "palavras_chave": ["feedback", "avaliação automática", "modelos de linguagem"],
        "autores": [{"nome": "Gabriel Ferraz", "email": "gabriel.ferraz@exemplo.edu.br", "instituicao": "UFAM"},
                    {"nome": "Sofia Ramos", "email": "sofia.ramos@exemplo.edu.br", "instituicao": "UFAM"}],
        "resumo": ("Turmas grandes de programação dificultam o retorno individual aos estudantes. "
                   "Investigamos o uso de modelos de linguagem para gerar feedback sobre submissões de "
                   "exercícios, combinando a saída de testes automáticos com instruções pedagógicas. "
                   "Em um experimento com 180 estudantes, o grupo que recebeu feedback gerado "
                   "corrigiu os erros em menos tentativas e avaliou o retorno como útil em 82% dos "
                   "casos. Discutimos riscos de respostas incorretas e formas de mitigá-los."),
        "qualidade": 0.9,
    },
    {
        "titulo": "Um framework de componentes para ambientes virtuais de aprendizagem",
        "trilha": "Computação Aplicada à Educação",
        "palavras_chave": ["ambiente virtual", "componentes", "aprendizagem"],
        "autores": [{"nome": "Paulo Henrique Dias", "email": "paulo.dias@exemplo.edu.br", "instituicao": "UFC"}],
        "resumo": ("Ambientes virtuais de aprendizagem são frequentemente reescritos para cada "
                   "instituição. Apresentamos um framework baseado em componentes de software que "
                   "permite montar um ambiente virtual escolhendo módulos de conteúdo, avaliação e "
                   "comunicação. Descrevemos os pontos de extensão do framework e duas instâncias "
                   "construídas a partir dele. A avaliação ainda é preliminar e se limita a uma "
                   "comparação do número de linhas escritas em cada instância."),
        "qualidade": 0.55,
    },
    {
        "titulo": "Escalonamento de tarefas na borda para aplicações sensíveis à latência",
        "trilha": "Sistemas Distribuídos",
        "palavras_chave": ["borda", "latência", "escalabilidade"],
        "autores": [{"nome": "Camila Torres", "email": "camila.torres@exemplo.edu.br", "instituicao": "UnB"}],
        "resumo": ("Aplicações como realidade aumentada exigem respostas em poucos milissegundos, o que "
                   "favorece o processamento na borda da rede. Este trabalho propõe uma heurística de "
                   "escalonamento que distribui tarefas entre dispositivos de borda considerando "
                   "latência e carga. Simulações com até 200 dispositivos indicam redução de 18% na "
                   "latência média, embora o custo de comunicação entre nós ainda não tenha sido medido."),
        "qualidade": 0.42,
    },
    {
        "titulo": "Testes de mutação aplicados a pipelines de dados",
        "trilha": "Engenharia de Software",
        "palavras_chave": ["testes", "qualidade de dados", "pipelines"],
        "autores": [{"nome": "Vitor Hugo Costa", "email": "vitor.costa@exemplo.edu.br", "instituicao": "UFG"}],
        "resumo": ("Pipelines de dados raramente têm testes que verifiquem a qualidade das "
                   "transformações. Discutimos a aplicação de testes de mutação a pipelines escritos "
                   "em Python, criando versões alteradas das transformações para verificar se os testes "
                   "existentes detectam as mudanças. Apresentamos os operadores de mutação propostos e "
                   "um exemplo ilustrativo; uma avaliação sistemática fica para trabalhos futuros."),
        "qualidade": 0.3,
    },
    {
        "titulo": "Previsão de evasão estudantil com aprendizado de máquina interpretável",
        "trilha": "Computação Aplicada à Educação",
        "palavras_chave": ["estudantes", "aprendizado de máquina", "evasão"],
        "autores": [{"nome": "Larissa Monteiro", "email": "larissa.monteiro@exemplo.edu.br", "instituicao": "UFRPE"}],
        "resumo": ("A evasão nos primeiros semestres é um problema persistente nos cursos de "
                   "computação. Treinamos modelos de aprendizado de máquina interpretáveis com dados "
                   "acadêmicos de 2.400 estudantes para prever o risco de evasão ao final do primeiro "
                   "período. O melhor modelo alcançou área sob a curva de 0,81, e as variáveis mais "
                   "relevantes foram reprovações em disciplinas introdutórias e frequência. Os "
                   "resultados apoiam ações de acompanhamento direcionadas."),
        "qualidade": 0.58,
    },
]
