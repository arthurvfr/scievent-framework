"""
Sobe todos os processos do SciEvent com um único comando.

    python iniciar.py                   sobe tudo e abre o navegador
    python iniciar.py --sem-navegador   sobe tudo sem abrir o navegador
    python iniciar.py --limpar          apaga os bancos (pasta data/) antes de subir

Cada microsserviço roda em um processo separado, na sua porta, e escreve
o log em logs/<servico>.log. Ctrl+C encerra todos.

(Alternativa manual, como no exemplo da disciplina: abrir um terminal por
serviço e rodar "python servicos/<nome>/app.py" e, por último,
"python gateway/app.py".)
"""
from __future__ import annotations

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import webbrowser

import requests

from scievent import config

RAIZ = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = {
    "registro": "servicos/registro/app.py",
    "eventos": "servicos/eventos/app.py",
    "submissoes": "servicos/submissoes/app.py",
    "revisoes": "servicos/revisoes/app.py",
    "programacao": "servicos/programacao/app.py",
    "notificacoes": "servicos/notificacoes/app.py",
    "agentes": "servicos/agentes/app.py",
    "gateway": "gateway/app.py",
}


def porta_ocupada(porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((config.HOST, porta)) == 0


def esperar_saude(nome: str, segundos: float) -> bool:
    url = f"http://{config.HOST}:{config.porta(nome)}/health"
    limite = time.time() + segundos
    while time.time() < limite:
        try:
            if requests.get(url, timeout=1).status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.3)
    return False


def _encerrar(*_):
    raise KeyboardInterrupt


def main() -> int:
    # Ctrl+C, fechamento da janela (Windows) e SIGTERM encerram todos os filhos.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    signal.signal(signal.SIGTERM, _encerrar)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _encerrar)

    parser = argparse.ArgumentParser(description="Sobe todos os microsserviços do SciEvent.")
    parser.add_argument("--sem-navegador", action="store_true", help="não abre o navegador")
    parser.add_argument("--limpar", action="store_true", help="apaga os bancos de dados antes de subir")
    args = parser.parse_args()

    if args.limpar:
        shutil.rmtree(config.PASTA_DADOS, ignore_errors=True)
        print("Bancos de dados apagados (pasta data/).")

    ocupadas = [(n, config.porta(n)) for n in SCRIPTS if porta_ocupada(config.porta(n))]
    if ocupadas:
        print("As portas abaixo já estão em uso. Feche a execução anterior e tente de novo:")
        for nome, porta in ocupadas:
            print(f"  - {nome}: {porta}")
        return 1

    os.makedirs(config.PASTA_LOGS, exist_ok=True)
    ambiente = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
                "PYTHONPATH": RAIZ + os.pathsep + os.environ.get("PYTHONPATH", "")}

    processos = []
    print("Iniciando os microsserviços do SciEvent...\n")
    for nome in config.ORDEM_INICIALIZACAO:
        log = open(os.path.join(config.PASTA_LOGS, f"{nome}.log"), "w", encoding="utf-8")
        processo = subprocess.Popen([sys.executable, os.path.join(RAIZ, SCRIPTS[nome])],
                                    cwd=RAIZ, env=ambiente, stdout=log, stderr=subprocess.STDOUT)
        processos.append((nome, processo, log))
        if nome == "registro":
            esperar_saude("registro", 15)

    print(f"{'SERVIÇO':<14}{'PORTA':<8}{'PID':<9}STATUS")
    print("-" * 44)
    falhas = 0
    for nome, processo, _ in processos:
        ok = esperar_saude(nome, 25)
        falhas += 0 if ok else 1
        status = "em execução" if ok else f"FALHOU (veja logs/{nome}.log)"
        print(f"{nome:<14}{config.porta(nome):<8}{processo.pid:<9}{status}")

    url = f"http://{config.HOST}:{config.porta('gateway')}"
    print(f"\nInterface web:      {url}")
    print(f"Microsserviços:     {url}/microservicos")
    print(f"API Gateway:        {url}/api")
    print("\nPressione Ctrl+C para encerrar todos os processos.")
    if falhas == 0 and not args.sem_navegador:
        webbrowser.open(url)

    try:
        while True:
            time.sleep(2)
            for nome, processo, _ in processos:
                if processo.poll() is not None:
                    print(f"\nAtenção: o processo '{nome}' terminou (código {processo.returncode}). "
                          f"Veja logs/{nome}.log")
                    raise KeyboardInterrupt
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        for _, processo, log in processos:
            if processo.poll() is None:
                processo.terminate()
        for _, processo, log in processos:
            try:
                processo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                processo.kill()
            log.close()
    print("Todos os processos foram encerrados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
