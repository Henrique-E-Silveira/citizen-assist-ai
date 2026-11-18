"""Leitura e validação das entradas do usuário.

Todas as funções repetem a pergunta até receber um valor válido, então uma
entrada inválida (letra, vazio, fora da faixa) nunca encerra o programa.
Quando a entrada vem de um arquivo (testes automáticos), o valor lido é
repetido na tela para que a saída sirva de evidência.
"""

import sys


class EntradaEncerrada(Exception):
    """Levantada quando a entrada termina (Ctrl+D ou fim de arquivo)."""


def ler(mensagem):
    """Lê uma linha digitada, sem espaços nas pontas."""
    try:
        valor = input(mensagem)
    except EOFError:
        raise EntradaEncerrada()
    if not sys.stdin.isatty():
        print(valor)  # repete a entrada quando ela não vem do teclado
    return valor.strip()


def ler_inteiro(mensagem, minimo, maximo):
    """Lê um número inteiro entre `minimo` e `maximo`."""
    while True:
        valor = ler(mensagem)
        if valor == "":
            print(f"  Atenção: resposta vazia. Digite um número de {minimo} a {maximo}.")
            continue
        if not valor.isdigit():
            print(f"  Atenção: digite apenas números (de {minimo} a {maximo}).")
            continue
        numero = int(valor)
        if numero < minimo or numero > maximo:
            print(f"  Atenção: opção fora da faixa. Escolha de {minimo} a {maximo}.")
            continue
        return numero


def ler_decimal(mensagem, minimo, maximo, padrao=None):
    """Lê um número com vírgula ou ponto. Se `padrao` existir, Enter usa o padrão."""
    while True:
        valor = ler(mensagem)
        if valor == "" and padrao is not None:
            return padrao
        if valor == "":
            print("  Atenção: resposta vazia. Digite um número.")
            continue
        try:
            numero = float(valor.replace(",", "."))
        except ValueError:
            print("  Atenção: digite um número (exemplo: 150 ou 0,90).")
            continue
        if numero < minimo or numero > maximo:
            print(f"  Atenção: o valor deve estar entre {minimo} e {maximo}.")
            continue
        return numero


def ler_sim_nao(mensagem):
    """Lê s ou n. Retorna True para sim e False para não."""
    while True:
        valor = ler(mensagem).lower()
        if valor in ("s", "sim"):
            return True
        if valor in ("n", "nao", "não"):
            return False
        print("  Atenção: responda com s (sim) ou n (não).")


def contem_dado_pessoal(texto):
    """Retorna True se o texto parece ter CPF, telefone ou e-mail.

    Regra da atividade: 8 ou mais dígitos (somando todos) ou o símbolo @.
    """
    quantidade_de_digitos = sum(1 for letra in texto if letra.isdigit())
    return quantidade_de_digitos >= 8 or "@" in texto


def formatar_numero(valor, casas=1):
    """Formata número no padrão brasileiro (vírgula decimal)."""
    return f"{valor:.{casas}f}".replace(".", ",")
