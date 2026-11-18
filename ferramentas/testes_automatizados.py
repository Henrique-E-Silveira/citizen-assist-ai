"""Testes automáticos do Citizen Assist AI (não usam o teclado nem alteram os arquivos reais).

Como executar (na pasta do projeto):
    python ferramentas/testes_automatizados.py
"""

import csv
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout

PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PASTA)

import energia  # noqa: E402
import entrada  # noqa: E402
from assistente import Assistente, calcular_indicadores  # noqa: E402
from base_conhecimento import BaseConhecimento, normalizar  # noqa: E402
from entrada import contem_dado_pessoal  # noqa: E402
from orientacao import Orientacao  # noqa: E402

CAMINHO_BASE = os.path.join(PASTA, "data", "base_conhecimento.json")
CAMINHO_PARAMETROS = os.path.join(PASTA, "data", "energia_parametros.json")
RESULTADOS = []


def base_real():
    base = BaseConhecimento(CAMINHO_BASE)
    base.carregar()
    return base


def silencioso(funcao, *args):
    with redirect_stdout(io.StringIO()):
        return funcao(*args)


def teste(codigo, descricao, funcao):
    try:
        ok = bool(funcao())
        detalhe = ""
    except Exception as e:  # um erro inesperado também reprova o teste
        ok = False
        detalhe = f" (erro: {type(e).__name__}: {e})"
    RESULTADOS.append((codigo, descricao, ok, detalhe))


# ----------------------------------------------------------------------
# Base de conhecimento e busca
# ----------------------------------------------------------------------
def testes_base():
    base = base_real()

    teste("T01", "normalizar tira acento, pontuação e maiúsculas",
          lambda: normalizar("Cartão do SUS?") == " cartao do sus ")

    def t02():
        sus = [o for o in base.orientacoes if o.id == 4][0]
        pontos = base.pontuar("Como faço o cartão do SUS?", sus)
        return pontos == 7 and base.confianca(pontos) == "ALTA"
    teste("T02", "exemplo do enunciado: 'Como faço o cartão do SUS?' = 7 pontos, confiança ALTA", t02)

    def t03():
        resultados = base.buscar("cartão do sus")
        return (isinstance(resultados[0], tuple) and isinstance(resultados[0][0], int)
                and isinstance(resultados[0][1], Orientacao)
                and all(resultados[i][0] >= resultados[i + 1][0] for i in range(len(resultados) - 1)))
    teste("T03", "buscar() devolve lista de tuplas (pontos, orientacao) da maior para a menor", t03)

    teste("T04", "pergunta sem relação não atinge 3 pontos",
          lambda: all(p < 3 for p, _ in base.buscar("quanto custa uma pizza grande")))

    teste("T05", "'bandeira vermelha' encontra a orientação 12 com confiança ALTA",
          lambda: base.buscar("bandeira vermelha")[0][1].id == 12
          and base.confianca(base.buscar("bandeira vermelha")[0][0]) == "ALTA")

    teste("T06", "'o que é tarifa social?' encontra a orientação 10",
          lambda: base.buscar("o que é tarifa social?")[0][1].id == 10)

    teste("T07", "palavras comuns (como, fazer, para) não geram pontos",
          lambda: base.buscar("como fazer para") == [])

    teste("T08", "'sus' só vale como palavra inteira (não ativa em 'sustentável')",
          lambda: all(o.id != 4 for _, o in base.buscar("energia sustentável")))

    teste("T09", "acentos na pergunta não atrapalham (CÁRTÃO SUS)",
          lambda: base.buscar("CÁRTÃO SUS")[0][1].id == 4 or base.buscar("CARTÃO SUS")[0][1].id == 4)

    teste("T10", "'luz do povo' ainda NÃO é encontrada (usada na alteração ao vivo do vídeo)",
          lambda: all(p < 3 for p, _ in base.buscar("o que é o luz do povo?")))

    def t11():
        base2 = base_real()
        for o in base2.orientacoes:
            if o.id == 10:
                o.palavras_chave.append("luz do povo")
        pontos, orient = base2.buscar("o que é o luz do povo?")[0]
        return orient.id == 10 and pontos >= 3
    teste("T11", "depois de incluir a palavra-chave 'luz do povo', a pergunta passa a ser encontrada", t11)

    def t12():
        formato = lambda d: len(d) == 10 and d[4] == "-" and d[7] == "-"
        return (len(base.orientacoes) >= 10 and len(base.categorias()) >= 3
                and all(len(o.palavras_chave) >= 3 for o in base.orientacoes)
                and all(o.fonte.startswith("https://") for o in base.orientacoes)
                and all(formato(o.verificado_em) for o in base.orientacoes)
                and all(o.documentos for o in base.orientacoes))
    teste("T12", "base cumpre os mínimos: 10+ orientações, 3+ categorias, 3+ palavras-chave, fonte e data", t12)


# ----------------------------------------------------------------------
# Dados pessoais e entradas inválidas
# ----------------------------------------------------------------------
def testes_entradas():
    teste("T13", "bloqueia CPF digitado com pontos", lambda: contem_dado_pessoal("meu cpf é 123.456.789-00"))
    teste("T14", "bloqueia telefone", lambda: contem_dado_pessoal("meu telefone é 11999998888"))
    teste("T15", "bloqueia e-mail (@)", lambda: contem_dado_pessoal("escreva para ana@email.com"))
    teste("T16", "não bloqueia pergunta normal com poucos números ('80 kWh')",
          lambda: not contem_dado_pessoal("o que é a gratuidade de 80 kWh?"))

    def com_respostas(respostas, funcao, *args):
        fila = iter(respostas)
        original = entrada.ler
        entrada.ler = lambda mensagem: next(fila)
        try:
            saida = io.StringIO()
            with redirect_stdout(saida):
                resultado = funcao(*args)
            return resultado, saida.getvalue().count("Atenção")
        finally:
            entrada.ler = original

    teste("T17", "menu: letra, vazio e fora da faixa não encerram (aceita 3)",
          lambda: com_respostas(["abc", "", "99", "3"], entrada.ler_inteiro, "op: ", 0, 5) == (3, 3))
    teste("T18", "s/n: resposta inválida pede de novo",
          lambda: com_respostas(["talvez", "S"], entrada.ler_sim_nao, "?") == (True, 1))
    teste("T19", "decimal: aceita vírgula, recusa texto e negativo",
          lambda: com_respostas(["abc", "-4", "0,90"], entrada.ler_decimal, "v: ", 0, 10) == (0.9, 2))


# ----------------------------------------------------------------------
# Arquivos ausentes ou corrompidos, histórico, indicadores e CSV
# ----------------------------------------------------------------------
def testes_arquivos():
    with tempfile.TemporaryDirectory() as pasta:
        def base_de(conteudo):
            caminho = os.path.join(pasta, "base.json")
            if conteudo is not None:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write(conteudo)
            elif os.path.exists(caminho):
                os.remove(caminho)
            b = BaseConhecimento(caminho)
            return b, b.carregar()

        def t20():
            b, ok = base_de(None)
            return ok is False and b.erro and b.orientacoes == []
        teste("T20", "base ausente não trava (mensagem de erro e base vazia)", t20)

        def t21():
            b, ok = base_de("{ isto nao e json")
            return ok is False and "corrompido" in b.erro
        teste("T21", "base corrompida não trava", t21)

        def t22():
            valido = json.load(open(CAMINHO_BASE, encoding="utf-8"))[0]
            b, ok = base_de(json.dumps([valido, {"id": 99}], ensure_ascii=False))
            return ok is True and len(b.orientacoes) == 1 and "ignorado" in b.erro
        teste("T22", "registro incompleto é ignorado; os válidos continuam", t22)

        def novo_assistente(historico_texto=None):
            caminho_h = os.path.join(pasta, "historico.json")
            for extra in (caminho_h, caminho_h + ".corrompido"):
                if os.path.exists(extra):
                    os.remove(extra)
            if historico_texto is not None:
                with open(caminho_h, "w", encoding="utf-8") as f:
                    f.write(historico_texto)
            return Assistente("Teste", base_real(), caminho_h,
                              os.path.join(pasta, "atendimentos.csv"), CAMINHO_PARAMETROS)

        def t23():
            a = silencioso(novo_assistente, "[[[ corrompido")
            return a.historico == [] and os.path.exists(os.path.join(pasta, "historico.json.corrompido"))
        teste("T23", "histórico corrompido não trava (cópia de segurança e histórico novo)", t23)

        def t24():
            a = novo_assistente()
            a.registrar("pergunta", "como tirar cpf", 2, True, True, 1, 3.2)
            salvo = json.load(open(os.path.join(pasta, "historico.json"), encoding="utf-8"))
            chaves = {"data", "origem", "pergunta", "id_orientacao", "encontrou", "ajudou", "tentativas", "tempo_segundos"}
            return len(salvo) == 1 and chaves.issubset(salvo[0].keys())
        teste("T24", "cada atendimento é salvo em historico.json com data, origem, pergunta, id, encontrou, ajudou, tentativas e tempo", t24)

        def t25():
            h = [
                {"sessao": "1", "origem": "pergunta", "pergunta": "a", "encontrou": True, "ajudou": True, "tentativas": 1, "tempo_segundos": 10.0, "facilidade": 4},
                {"sessao": "1", "origem": "pergunta", "pergunta": "b", "encontrou": False, "ajudou": False, "tentativas": 3, "tempo_segundos": 30.0, "facilidade": 4},
                {"sessao": "2", "origem": "categoria", "pergunta": "c", "encontrou": True, "ajudou": False, "tentativas": 2, "tempo_segundos": 20.0, "facilidade": 5},
                {"sessao": "2", "origem": "energia", "pergunta": "d", "encontrou": True, "ajudou": True, "tentativas": 1, "tempo_segundos": 40.0, "facilidade": 5},
            ]
            i = calcular_indicadores(h)
            return (i["total"] == 4 and i["resposta_encontrada_pct"] == 75.0 and i["taxa_acerto_pct"] == 50.0
                    and abs(i["tempo_medio_s"] - 70 / 3) < 1e-9 and i["tentativas_media"] == 1.75
                    and i["facilidade_media"] == 4.5 and i["sessoes_avaliadas"] == 2
                    and i["duvidas_sem_solucao"] == ["b"])
        teste("T25", "indicadores calculados corretamente (encontrada, acerto, tempo, tentativas, facilidade, sem solução)", t25)

        teste("T26", "indicadores com histórico vazio não dão erro", lambda: calcular_indicadores([]) == {"total": 0})

        def t27():
            a = novo_assistente()
            a.registrar("pergunta", "como tirar cpf", 2, True, True, 1, 3.2)
            a.registrar("pergunta", "luz do povo", None, False, False, 2, 8.0)
            silencioso(a.exportar_csv)
            with open(os.path.join(pasta, "atendimentos.csv"), encoding="utf-8-sig", newline="") as f:
                linhas = list(csv.DictReader(f))
            return len(linhas) == 2 and linhas[1]["pergunta"] == "luz do povo" and linhas[0]["id_orientacao"] == "2"
        teste("T27", "CSV exportado com csv.DictWriter tem os atendimentos e pode ser lido de volta", t27)


# ----------------------------------------------------------------------
# Energia (SERS)
# ----------------------------------------------------------------------
def testes_energia():
    valores, detalhes, aviso = energia.carregar_parametros(CAMINHO_PARAMETROS)

    teste("T28", "parâmetros de energia carregados com fonte e tipo",
          lambda: aviso is None and all("fonte" in v and v["tipo"] in ("oficial", "estimativa") for v in detalhes.values()))

    def t29():
        r = energia.analisar([150, 140, 160], 0.90, 1, False, 5, 5, 3, 10, 5500, valores)
        ts, ef, solar = r["alternativas"]
        return (abs(ts["economia_mensal"] - 72.0) < 1e-9 and abs(ef["custo_inicial"] - 50.0) < 1e-9
                and abs(solar["custo_inicial"] - 3155.5555) < 0.01 and abs(solar["kwp"] - 1.1111) < 0.001)
    teste("T29", "cálculos: Tarifa Social R$ 72,00; LED R$ 50,00; solar 1,11 kWp e R$ 3.155,56 (consumo médio 150 kWh)", t29)

    def t30():
        r = energia.analisar([70, 75, 72], 0.90, 1, True, 0, 5, 0, 10, 5500, valores)
        solar = [a for a in r["alternativas"] if "solar" in a["nome"]][0]
        return solar["viabilidade"].startswith("NÃO COMPENSA")
    teste("T30", "família com Tarifa Social e consumo baixo: solar 'NÃO COMPENSA'", t30)

    def t31():
        r = energia.analisar([150, 150, 150], 0.90, 3, False, 0, 5, 0, 10, 5500, valores)
        ef = [a for a in r["alternativas"] if a["nome"].startswith("Eficiência")][0]
        return ef["viabilidade"].startswith("NÃO SE APLICA") and ef["economia_kwh"] == 0
    teste("T31", "sem lâmpadas incandescentes nem banho elétrico: eficiência 'NÃO SE APLICA'", t31)

    def t32():
        r = energia.analisar([150, 150, 150], 0.90, 1, False, 5, 5, 3, 10, 5500, valores)
        return r["recomendada"]["nome"].startswith("Tarifa Social")
    teste("T32", "quem tem direito à Tarifa Social recebe essa alternativa como primeira sugestão", t32)

    def t33():
        r = energia.analisar([300, 310, 290], 0.90, 3, False, 0, 5, 0, 10, 5500, valores)
        nomes = [a["nome"] for a in r["alternativas"]]
        return not any(n.startswith(("Tarifa", "Desconto")) for n in nomes) and r["recomendada"]["nome"].startswith("Energia solar")
    teste("T33", "renda acima de 1 salário mínimo: sem Tarifa/Desconto Social; solar é a sugestão", t33)

    def t34():
        v, d, av = energia.carregar_parametros(os.path.join(PASTA, "nao_existe.json"))
        return av is not None and v["limite_gratuidade_tarifa_social_kwh"] == 80
    teste("T34", "arquivo de parâmetros ausente usa valores padrão e avisa", t34)

    teste("T35", "CO2 evitado = kWh economizados x 12 meses x fator (solar, 120 kWh/mês)",
          lambda: abs(energia.alternativa_solar(150, 0.9, False, valores)["co2_kg_ano"] - 120 * 12 * 0.0385) < 1e-9)


def main():
    testes_base()
    testes_entradas()
    testes_arquivos()
    testes_energia()
    aprovados = 0
    for codigo, descricao, ok, detalhe in RESULTADOS:
        print(f"{codigo} [{'OK   ' if ok else 'FALHA'}] {descricao}{detalhe}")
        aprovados += ok
    print(f"\nResultado: {aprovados} de {len(RESULTADOS)} testes aprovados.")
    return 0 if aprovados == len(RESULTADOS) else 1


if __name__ == "__main__":
    sys.exit(main())
