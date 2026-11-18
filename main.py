"""Citizen Assist AI - assistente de orientação para famílias de baixa renda.

Global Solution 2026.2 | Pensamento Computacional e Automação com Python
e Soluções em Energias Renováveis e Sustentáveis | FIAP

Como executar:
    python main.py
"""

import os
import sys

import entrada
from assistente import Assistente
from base_conhecimento import BaseConhecimento
from entrada import EntradaEncerrada

PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))


def pasta_de_dados():
    """Usa data/ por padrão. A opção --data-dir serve para testes."""
    if "--data-dir" in sys.argv:
        posicao = sys.argv.index("--data-dir")
        if posicao + 1 < len(sys.argv):
            return sys.argv[posicao + 1]
    return os.path.join(PASTA_PROJETO, "data")


def arquivo_de_dados(pasta, nome):
    """Usa o arquivo da pasta escolhida; se não existir, usa o arquivo padrão de data/."""
    escolhido = os.path.join(pasta, nome)
    if os.path.exists(escolhido):
        return escolhido
    return os.path.join(PASTA_PROJETO, "data", nome)


def mostrar_menu(assistente):
    print()
    print("=== CITIZEN ASSIST AI ===")
    print("Orientações para famílias de baixa renda: documentos, saúde, benefícios, energia e consumo.")
    print("Aviso: este assistente NÃO é um canal oficial. Não digite CPF, telefone ou e-mail.")
    print("  1) Perguntar (texto livre)")
    print("  2) Navegar por categorias")
    print("  3) Calculadora de energia (economia e energia solar)")
    print("  4) Ver indicadores")
    print("  5) Exportar atendimentos para CSV")
    print("  0) Sair")


def main():
    pasta = pasta_de_dados()
    os.makedirs(pasta, exist_ok=True)

    base = BaseConhecimento(arquivo_de_dados(pasta, "base_conhecimento.json"))
    base.carregar()  # lê o JSON e cria os objetos Orientacao
    if base.erro:
        print(f"Atenção: {base.erro}")

    assistente = Assistente(
        "Citizen Assist AI", base,
        caminho_historico=os.path.join(pasta, "historico.json"),
        caminho_csv=os.path.join(pasta, "atendimentos.csv"),
        caminho_energia=arquivo_de_dados(pasta, "energia_parametros.json"),
    )

    try:
        while True:
            mostrar_menu(assistente)
            opcao = entrada.ler_inteiro("Escolha uma opção: ", 0, 5)
            if opcao == 1:
                assistente.perguntar()
            elif opcao == 2:
                assistente.navegar()
            elif opcao == 3:
                assistente.calcular_energia()
            elif opcao == 4:
                assistente.indicadores()
            elif opcao == 5:
                assistente.exportar_csv()
            elif opcao == 0:
                assistente.encerrar()
                break
    except EntradaEncerrada:
        print("\nEntrada encerrada. Finalizando o programa.")
        assistente.salvar_historico()
    except KeyboardInterrupt:
        print("\nPrograma interrompido. Até logo!")
        assistente.salvar_historico()


if __name__ == "__main__":
    main()
