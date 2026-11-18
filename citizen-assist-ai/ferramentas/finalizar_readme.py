"""Preenche o README com os dados reais (links, fontes e resultado do teste com usuários).

Rode depois dos testes com as pessoas e depois de subir os vídeos:

    python ferramentas/finalizar_readme.py --repo URL_DO_GITHUB --video-pcp URL_YOUTUBE --video-sers URL_YOUTUBE --melhoria "O que vocês melhoraram a partir do teste"

Todas as opções são opcionais. Os números vêm de data/historico.json (nada é inventado).
"""

import argparse
import json
import os
import sys

PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PASTA)

from assistente import calcular_indicadores, formatar_indicadores  # noqa: E402

README = os.path.join(PASTA, "README.md")


def trocar_bloco(texto, marca, novo):
    inicio = f"<!-- {marca}-INICIO -->"
    fim = f"<!-- {marca}-FIM -->"
    if inicio not in texto or fim not in texto:
        print(f"Aviso: marcador {marca} não encontrado no README.")
        return texto
    antes = texto.split(inicio)[0]
    depois = texto.split(fim)[1]
    return f"{antes}{inicio}\n{novo}\n{fim}{depois}"


def carregar_json(caminho, padrao):
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, ValueError):
        return padrao


def main():
    parser = argparse.ArgumentParser(description="Preenche o README com dados reais.")
    parser.add_argument("--repo", help="link do repositório no GitHub")
    parser.add_argument("--video-pcp", help="link do vídeo técnico (PCP) no YouTube")
    parser.add_argument("--video-sers", help="link do vídeo pitch (SERS) no YouTube")
    parser.add_argument("--melhoria", help="melhoria feita a partir do teste com usuários")
    args = parser.parse_args()

    with open(README, "r", encoding="utf-8") as arquivo:
        texto = arquivo.read()

    # ---- links (mantém o que já estava, se a opção não for informada)
    atual = {}
    inicio, fim = "<!-- LINKS-INICIO -->", "<!-- LINKS-FIM -->"
    if inicio in texto and fim in texto:
        for linha in texto.split(inicio)[1].split(fim)[0].splitlines():
            if ": " in linha and "http" in linha:
                nome, valor = linha.lstrip("- ").split(": ", 1)
                atual[nome] = valor
    pendente = "(será preenchido por `ferramentas/finalizar_readme.py`)"
    links = {
        "Repositório GitHub": args.repo or atual.get("Repositório GitHub") or pendente,
        "Vídeo técnico do PCP (YouTube, não listado)": args.video_pcp or atual.get("Vídeo técnico do PCP (YouTube, não listado)") or pendente,
        "Vídeo pitch do SERS (YouTube, não listado)": args.video_sers or atual.get("Vídeo pitch do SERS (YouTube, não listado)") or pendente,
    }
    texto = trocar_bloco(texto, "LINKS", "\n".join(f"- {n}: {v}" for n, v in links.items()))

    # ---- fontes
    base = carregar_json(os.path.join(PASTA, "data", "base_conhecimento.json"), [])
    linhas = ["| ID | Orientação | Fonte oficial | Verificado em |", "|---|---|---|---|"]
    for o in base:
        linhas.append(f"| {o['id']} | {o['titulo']} | {o['fonte']} | {o['verificado_em']} |")
    texto = trocar_bloco(texto, "FONTES", "\n".join(linhas))

    # ---- resultado do teste
    historico = carregar_json(os.path.join(PASTA, "data", "historico.json"), [])
    if historico:
        ind = calcular_indicadores(historico)
        sessoes = {a.get("sessao") for a in historico}
        datas = sorted(a["data"][:10] for a in historico if a.get("data"))
        energia = [a for a in historico if a.get("origem") == "energia"]
        ajudou_energia = sum(1 for a in energia if a.get("ajudou") is True)
        bloco = [f"**Período dos testes:** {datas[0]} a {datas[-1]}." if datas else "", "",
                 f"**Pessoas (sessões):** {len(sessoes)} | **Atendimentos:** {len(historico)}.", "",
                 "| Indicador | Resultado |", "|---|---|"]
        for linha in formatar_indicadores(ind):
            if ": " in linha and not linha.startswith(" ") and "Atendimentos registrados" not in linha \
                    and "Dúvidas sem solução" not in linha:
                nome, valor = linha.split(": ", 1)
                bloco.append(f"| {nome} | {valor} |")
        bloco.append("")
        if energia:
            bloco.append(f"**Simulações de energia (SERS):** {len(energia)}; ajudou em {ajudou_energia} "
                         f"({100 * ajudou_energia / len(energia):.0f}%).")
            bloco.append("")
        if ind["duvidas_sem_solucao"]:
            bloco.append("**Dúvidas sem solução:**")
            bloco.extend(f"- {d}" for d in ind["duvidas_sem_solucao"])
        else:
            bloco.append("**Dúvidas sem solução:** nenhuma.")
        bloco.append("")
        bloco.append("**Melhoria feita a partir do teste:** " + (args.melhoria or "(informe com a opção --melhoria)"))
        texto = trocar_bloco(texto, "RESULTADO", "\n".join(bloco))
        if len(historico) < 10 or len(sessoes) < 3:
            print(f"Atenção: o enunciado pede 3 pessoas e 10 atendimentos. "
                  f"Hoje há {len(sessoes)} sessão(ões) e {len(historico)} atendimento(s).")
    else:
        print("Aviso: data/historico.json está vazio. A seção de resultado não foi alterada.")

    with open(README, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
    print("README atualizado.")


if __name__ == "__main__":
    main()
