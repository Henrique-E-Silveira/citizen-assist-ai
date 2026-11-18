"""Classe BaseConhecimento: o conjunto de todas as orientações.

Lê o JSON, lista categorias e busca a melhor orientação por pontuação.
"""

import json

from orientacao import Orientacao

# ----------------------------------------------------------------------
# Regras de pontuação (explicadas no README)
# ----------------------------------------------------------------------
PONTOS_PALAVRA_CHAVE = 3      # palavra-chave da orientação aparece na pergunta
PONTOS_TITULO = 1             # palavra da pergunta (4+ letras) aparece no título
PONTOS_CONFIANCA_ALTA = 6     # 6 pontos ou mais
PONTOS_MINIMOS = 3            # abaixo disso: "não encontrei"

# Palavras comuns que não ajudam a achar o assunto (evitam pontos "falsos" no título)
PALAVRAS_IGNORADAS = {"como", "para", "quero", "preciso", "posso", "fazer", "qual",
                      "quais", "onde", "quando", "tenho", "sobre", "minha", "meus",
                      "minhas", "esta", "esse", "essa", "isso", "mais", "pode",
                      "porque", "quem"}

ACENTOS = {"á": "a", "à": "a", "ã": "a", "â": "a", "é": "e", "ê": "e",
           "í": "i", "ó": "o", "õ": "o", "ô": "o", "ú": "u", "ü": "u", "ç": "c"}


def normalizar(texto):
    """Deixa o texto em minúsculas, sem acentos e sem pontuação.

    O resultado começa e termina com espaço, para que a busca encontre
    palavras inteiras (" sus " não aparece dentro de " sustentavel ").
    """
    texto = texto.lower().strip()
    for letra, troca in ACENTOS.items():
        texto = texto.replace(letra, troca)
    for sinal in '?!.,;:()/-"\'':
        texto = texto.replace(sinal, " ")
    return " " + " ".join(texto.split()) + " "


class BaseConhecimento:
    """Carrega as orientações do JSON e responde buscas."""

    def __init__(self, caminho):
        self.caminho = caminho
        self.orientacoes = []   # lista de objetos Orientacao
        self.erro = None        # mensagem de erro, se o arquivo não pôde ser lido

    def carregar(self):
        """Lê o JSON e cria os objetos Orientacao. Nunca trava o programa.

        Retorna True se carregou pelo menos uma orientação.
        """
        self.orientacoes = []
        self.erro = None
        try:
            with open(self.caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except FileNotFoundError:
            self.erro = f"Arquivo da base não encontrado: {self.caminho}"
            return False
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            self.erro = f"Arquivo da base está corrompido ou ilegível ({e})."
            return False

        if not isinstance(dados, list):
            self.erro = "A base deve ser uma lista de orientações."
            return False

        ignoradas = 0
        ids_vistos = set()
        for registro in dados:
            try:
                orientacao = Orientacao.de_dicionario(registro)
            except (ValueError, TypeError):
                ignoradas += 1
                continue
            if orientacao.id in ids_vistos:
                ignoradas += 1
                continue
            ids_vistos.add(orientacao.id)
            self.orientacoes.append(orientacao)

        if ignoradas:
            self.erro = f"{ignoradas} registro(s) inválido(s) ou repetido(s) foram ignorados."
        if not self.orientacoes:
            self.erro = "Nenhuma orientação válida foi encontrada na base."
            return False
        return True

    def categorias(self):
        """Lista as categorias (sem repetir), em ordem alfabética."""
        return sorted({o.categoria for o in self.orientacoes})

    def por_categoria(self, categoria):
        """Lista as orientações de uma categoria."""
        return [o for o in self.orientacoes if o.categoria == categoria]

    def pontuar(self, pergunta, orientacao):
        """Calcula a pontuação de uma orientação para a pergunta.

        +3 por palavra-chave que aparece na pergunta;
        +1 por palavra da pergunta (4 letras ou mais) que aparece no título.
        """
        pergunta_normalizada = normalizar(pergunta)
        pontos = 0
        for palavra_chave in orientacao.palavras_chave:
            if normalizar(palavra_chave) in pergunta_normalizada:
                pontos += PONTOS_PALAVRA_CHAVE
        titulo_normalizado = normalizar(orientacao.titulo)
        for palavra in set(pergunta_normalizada.split()):
            if len(palavra) >= 4 and palavra not in PALAVRAS_IGNORADAS:
                if " " + palavra + " " in titulo_normalizado:
                    pontos += PONTOS_TITULO
        return pontos

    def buscar(self, pergunta):
        """Devolve uma lista de tuplas (pontos, orientacao), da maior para a menor.

        Só entram orientações com pelo menos 1 ponto.
        """
        resultados = []
        for orientacao in self.orientacoes:
            pontos = self.pontuar(pergunta, orientacao)
            if pontos > 0:
                resultados.append((pontos, orientacao))
        resultados.sort(key=lambda tupla: (-tupla[0], tupla[1].id))
        return resultados

    @staticmethod
    def confianca(pontos):
        """Traduz a pontuação em nível de confiança."""
        if pontos >= PONTOS_CONFIANCA_ALTA:
            return "ALTA"
        if pontos >= PONTOS_MINIMOS:
            return "MÉDIA"
        return None
