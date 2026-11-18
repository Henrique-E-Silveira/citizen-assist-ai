"""Classe Assistente: quem conversa com o cidadão.

Faz o atendimento (pergunta livre e navegação por categorias), guarda o
histórico em JSON, calcula os indicadores e exporta o CSV.
"""

import csv
import json
import os
import time
from datetime import datetime

import energia
import entrada
from entrada import formatar_numero as fmt
from base_conhecimento import BaseConhecimento

AVISO = "este assistente NÃO é um canal oficial."

CAMPOS_CSV = ["data", "sessao", "origem", "pergunta", "perguntas_digitadas", "id_orientacao",
              "encontrou", "ajudou", "tentativas", "tempo_segundos", "facilidade"]


def calcular_indicadores(historico):
    """Calcula os indicadores a partir da lista de atendimentos.

    Retorna um dicionário com os números (ou None onde não há dados).
    """
    total = len(historico)
    if total == 0:
        return {"total": 0}

    encontrados = [a for a in historico if a.get("encontrou")]
    ajudaram = [a for a in historico if a.get("ajudou") is True]

    tempos = [a["tempo_segundos"] for a in encontrados if a.get("tempo_segundos") is not None]
    tentativas = [a["tentativas"] for a in historico if a.get("tentativas") is not None]

    # A nota de facilidade é uma por sessão: tira a média por sessão.
    notas_por_sessao = {}
    for a in historico:
        if a.get("facilidade") is not None:
            notas_por_sessao[a.get("sessao")] = a["facilidade"]
    notas = list(notas_por_sessao.values())

    sem_solucao = []
    for a in historico:
        if a.get("origem") == "pergunta" and (not a.get("encontrou") or a.get("ajudou") is False):
            if a.get("pergunta") and a["pergunta"] not in sem_solucao:
                sem_solucao.append(a["pergunta"])

    return {
        "total": total,
        "resposta_encontrada_pct": 100 * len(encontrados) / total,
        "taxa_acerto_pct": 100 * len(ajudaram) / total,
        "tempo_medio_s": sum(tempos) / len(tempos) if tempos else None,
        "tentativas_media": sum(tentativas) / len(tentativas) if tentativas else None,
        "facilidade_media": sum(notas) / len(notas) if notas else None,
        "sessoes_avaliadas": len(notas),
        "duvidas_sem_solucao": sem_solucao,
    }


def formatar_indicadores(ind):
    """Transforma o dicionário de indicadores em linhas de texto."""
    if ind["total"] == 0:
        return ["Ainda não há atendimentos registrados."]

    def num(valor, casas=1, sufixo=""):
        return "sem dados" if valor is None else fmt(valor, casas) + sufixo

    linhas = [
        f"Atendimentos registrados: {ind['total']}",
        f"Resposta encontrada (%): {num(ind['resposta_encontrada_pct'])}",
        f"Taxa de acerto, ajudou (%): {num(ind['taxa_acerto_pct'])}",
        f"Tempo médio para encontrar (s): {num(ind['tempo_medio_s'])}",
        f"Tentativas por atendimento: {num(ind['tentativas_media'], 2)}",
        f"Facilidade de uso (1 a 5): {num(ind['facilidade_media'], 2)} "
        f"({ind['sessoes_avaliadas']} sessão(ões) avaliada(s))",
    ]
    if ind["duvidas_sem_solucao"]:
        linhas.append(f"Dúvidas sem solução ({len(ind['duvidas_sem_solucao'])}):")
        for duvida in ind["duvidas_sem_solucao"]:
            linhas.append(f"  - {duvida}")
    else:
        linhas.append("Dúvidas sem solução: nenhuma")
    return linhas


class Assistente:
    """Conversa com o cidadão, guarda o histórico e calcula os indicadores."""

    def __init__(self, nome, base, caminho_historico, caminho_csv, caminho_energia):
        self.nome = nome
        self.base = base                      # composição: o assistente TEM uma base
        self.caminho_historico = caminho_historico
        self.caminho_csv = caminho_csv
        self.caminho_energia = caminho_energia
        self.sessao = datetime.now().strftime("%Y%m%d%H%M%S")
        self.historico = []
        self.carregar_historico()

    # ------------------------------------------------------------------
    # Histórico
    # ------------------------------------------------------------------
    def carregar_historico(self):
        """Lê data/historico.json. Arquivo ausente ou corrompido não trava o programa."""
        self.historico = []
        if not os.path.exists(self.caminho_historico):
            return
        try:
            with open(self.caminho_historico, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            if not isinstance(dados, list):
                raise ValueError("o histórico deve ser uma lista")
            self.historico = [d for d in dados if isinstance(d, dict)]
        except (OSError, ValueError, UnicodeDecodeError) as e:
            print(f"Atenção: o histórico estava ilegível ({e}). Começando um histórico novo.")
            try:
                os.replace(self.caminho_historico, self.caminho_historico + ".corrompido")
            except OSError:
                pass
            self.historico = []

    def salvar_historico(self):
        try:
            with open(self.caminho_historico, "w", encoding="utf-8") as arquivo:
                json.dump(self.historico, arquivo, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"Atenção: não foi possível salvar o histórico ({e}).")

    def registrar(self, origem, pergunta, id_orientacao, encontrou, ajudou, tentativas, tempo,
                  perguntas_digitadas=None):
        """Guarda um atendimento no histórico (e no arquivo)."""
        registro = {
            "data": datetime.now().isoformat(timespec="seconds"),
            "sessao": self.sessao,
            "origem": origem,                 # "pergunta", "categoria" ou "energia"
            "pergunta": pergunta,
            "perguntas_digitadas": perguntas_digitadas if perguntas_digitadas else [pergunta],
            "id_orientacao": id_orientacao,
            "encontrou": encontrou,
            "ajudou": ajudou,
            "tentativas": tentativas,
            "tempo_segundos": tempo,
            "facilidade": None,
        }
        self.historico.append(registro)
        self.salvar_historico()

    # ------------------------------------------------------------------
    # Atendimento por pergunta livre
    # ------------------------------------------------------------------
    def perguntar(self):
        print("\n--- Perguntar ao assistente ---")
        print(f"Aviso: {AVISO} Não digite CPF, telefone ou e-mail.")
        inicio = time.time()
        tentativas = 0
        ultima_pergunta = ""
        digitadas = []   # tudo o que a pessoa digitou neste atendimento (sem dados pessoais)

        while True:
            texto = entrada.ler("Digite sua dúvida (0 para voltar): ")
            if texto == "0":
                if tentativas > 0:  # desistiu sem resolver: vira "dúvida sem solução"
                    self.registrar("pergunta", ultima_pergunta, None, False, False,
                                   tentativas, round(time.time() - inicio, 1), digitadas)
                return
            if texto == "":
                print("Atenção: a resposta está vazia. Digite sua dúvida ou 0 para voltar.")
                continue
            if entrada.contem_dado_pessoal(texto):
                # Não registra e não conta como tentativa
                print("Atenção: não digite CPF, telefone ou e-mail. Reescreva.")
                continue

            tentativas += 1
            ultima_pergunta = texto
            digitadas.append(texto)
            resultados = [r for r in self.base.buscar(texto) if r[0] >= 3]

            if not resultados:
                print("Não encontrei uma orientação para essa dúvida.")
                print("Tente outras palavras (por exemplo: cpf, cartão sus, tarifa social) ou use a navegação por categorias.")
                print("Categorias: " + ", ".join(self.base.categorias()))
                continue

            pontos, melhor = resultados[0]
            print(f"\nConfiança da resposta: {self.base.confianca(pontos)} ({pontos} pontos)")
            melhor.exibir()
            alternativas = resultados[1:3]
            if alternativas:
                print("Outras orientações que podem ajudar:")
                for pts, alternativa in alternativas:
                    print(f"  - {alternativa.titulo} ({pts} pontos)")
                print()

            if entrada.ler_sim_nao("Essa orientação respondeu sua dúvida? (s/n): "):
                self.registrar("pergunta", texto, melhor.id, True, True,
                               tentativas, round(time.time() - inicio, 1), digitadas)
                return
            if entrada.ler_sim_nao("Quer tentar de novo com outras palavras? (s/n): "):
                continue
            self.registrar("pergunta", texto, melhor.id, True, False,
                           tentativas, round(time.time() - inicio, 1), digitadas)
            return

    # ------------------------------------------------------------------
    # Navegação por categorias
    # ------------------------------------------------------------------
    def navegar(self):
        categorias = self.base.categorias()
        if not categorias:
            print("A base de conhecimento está vazia. Não há categorias para mostrar.")
            return
        while True:
            print("\n--- Categorias ---")
            for numero, categoria in enumerate(categorias, start=1):
                quantidade = len(self.base.por_categoria(categoria))
                print(f"  {numero}) {categoria} ({quantidade})")
            print("  0) Voltar")
            escolha = entrada.ler_inteiro("Escolha uma categoria: ", 0, len(categorias))
            if escolha == 0:
                return
            self._navegar_orientacoes(categorias[escolha - 1])

    def _navegar_orientacoes(self, categoria):
        orientacoes = self.base.por_categoria(categoria)
        while True:
            inicio = time.time()
            print(f"\n--- {categoria} ---")
            for numero, orientacao in enumerate(orientacoes, start=1):
                print(f"  {numero}) {orientacao.titulo}")
            print("  0) Voltar")
            escolha = entrada.ler_inteiro("Escolha uma orientação: ", 0, len(orientacoes))
            if escolha == 0:
                return
            orientacao = orientacoes[escolha - 1]
            orientacao.exibir()
            ajudou = entrada.ler_sim_nao("Essa orientação respondeu sua dúvida? (s/n): ")
            self.registrar("categoria", orientacao.titulo, orientacao.id, True, ajudou,
                           1, round(time.time() - inicio, 1))

    # ------------------------------------------------------------------
    # Energia (SERS)
    # ------------------------------------------------------------------
    def calcular_energia(self):
        inicio = time.time()
        resultado = energia.executar(self.caminho_energia)
        if resultado is None:
            return
        self.registrar("energia", "Simulação de energia (consumo, economia e energia solar)",
                       None, True, resultado["ajudou"], 1, round(time.time() - inicio, 1))

    # ------------------------------------------------------------------
    # Indicadores e CSV
    # ------------------------------------------------------------------
    def indicadores(self):
        print("\n=== Indicadores ===")
        for linha in formatar_indicadores(calcular_indicadores(self.historico)):
            print(linha)

    def exportar_csv(self):
        """Exporta todos os atendimentos para data/atendimentos.csv (csv.DictWriter)."""
        try:
            with open(self.caminho_csv, "w", encoding="utf-8-sig", newline="") as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CSV, extrasaction="ignore")
                escritor.writeheader()
                for atendimento in self.historico:
                    linha = dict(atendimento)
                    digitadas = linha.get("perguntas_digitadas")
                    if isinstance(digitadas, list):
                        linha["perguntas_digitadas"] = " | ".join(digitadas)
                    escritor.writerow(linha)
        except OSError as e:
            print(f"Atenção: não foi possível exportar o CSV ({e}).")
            return False
        print(f"{len(self.historico)} atendimento(s) exportado(s) para {os.path.basename(self.caminho_csv)}.")
        return True

    # ------------------------------------------------------------------
    # Encerramento
    # ------------------------------------------------------------------
    def encerrar(self):
        """Pede a nota de facilidade (1 a 5), salva e exporta o CSV."""
        da_sessao = [a for a in self.historico if a.get("sessao") == self.sessao]
        if da_sessao:
            print("\nObrigado por usar o assistente!")
            nota = entrada.ler_inteiro(
                "De 1 a 5, qual a facilidade de uso? (1 = muito difícil, 5 = muito fácil): ", 1, 5)
            for atendimento in da_sessao:
                atendimento["facilidade"] = nota
            self.salvar_historico()
            self.exportar_csv()
        print(f"Aviso: {AVISO}")
