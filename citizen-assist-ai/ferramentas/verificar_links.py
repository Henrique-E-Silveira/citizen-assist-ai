"""Confere se os links das fontes (base de conhecimento e parâmetros de energia) abrem.

Precisa de internet:
    python ferramentas/verificar_links.py

Se algum link mostrar 403 ou 429, isso costuma ser bloqueio de robô: abra o link no navegador.
Se mostrar 404 (página não encontrada), troque o link pela página oficial correta e
atualize o campo "verificado_em" depois de conferir o conteúdo.
"""

import json
import os
import urllib.error
import urllib.request

PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def links():
    encontrados = {}
    with open(os.path.join(PASTA, "data", "base_conhecimento.json"), encoding="utf-8") as f:
        for o in json.load(f):
            encontrados.setdefault(o["fonte"], []).append(f"orientação {o['id']}")
    with open(os.path.join(PASTA, "data", "energia_parametros.json"), encoding="utf-8") as f:
        for nome, info in json.load(f)["parametros"].items():
            if info["fonte"].startswith("http"):
                encontrados.setdefault(info["fonte"], []).append(f"parâmetro {nome}")
    return encontrados


def testar(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (verificador de links)"})
    try:
        with urllib.request.urlopen(pedido, timeout=20) as resposta:
            return f"OK ({resposta.status})"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:  # sem internet, tempo esgotado etc.
        return f"ERRO ({type(e).__name__})"


if __name__ == "__main__":
    for url, usos in links().items():
        print(f"{testar(url):<14} {url}\n               usado em: {', '.join(usos)}")
