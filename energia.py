"""Módulo de energia (SERS): uso consciente de energia dentro do Citizen Assist AI.

A pessoa informa o consumo da conta de luz e o assistente:
1. analisa o consumo (média, último mês e comparação com os 80 kWh da Tarifa Social);
2. compara alternativas de economia ou fornecimento de energia:
   - Tarifa Social / Desconto Social (direito, sem custo);
   - Eficiência energética (lâmpada LED e banho);
   - Energia solar fotovoltaica (fonte renovável);
3. justifica com custos, retorno do investimento, viabilidade e impacto ambiental (CO2).

Os valores usados ficam em data/energia_parametros.json, com fonte e tipo
(oficial ou estimativa). Os resultados são ESTIMATIVAS educativas.
"""

import json
import os

from entrada import formatar_numero as fmt
from entrada import ler_decimal, ler_inteiro, ler_sim_nao

AVISO_ENERGIA = ("Estimativas educativas. Não substituem orçamento de empresa instaladora "
                 "nem a análise da sua distribuidora. Este assistente NÃO é canal oficial.")

# Valores usados se o arquivo de parâmetros não puder ser lido
PARAMETROS_PADRAO = {
    "limite_gratuidade_tarifa_social_kwh": 80,
    "limite_desconto_social_kwh": 120,
    "custo_disponibilidade_kwh": 30,
    "lampada_incandescente_w": 60,
    "lampada_led_w": 9,
    "preco_lampada_led_reais": 10.0,
    "reducao_chuveiro_posicao_verao": 0.30,
    "minutos_a_menos_no_banho": 2,
    "irradiacao_media_kwh_m2_dia": 4.5,
    "eficiencia_sistema_solar": 0.80,
    "preco_sistema_solar_reais_por_wp": 2.84,
    "fator_emissao_kg_co2_por_kwh": 0.0385,
    "tarifa_exemplo_reais_kwh": 0.90,
    "retorno_maximo_viavel_meses": 96,
}

DIAS_NO_MES = 30


def carregar_parametros(caminho):
    """Lê os parâmetros do JSON. Se falhar, usa os valores padrão.

    Retorna (valores, detalhes, aviso): `valores` é {nome: número};
    `detalhes` é {nome: dicionário com fonte e tipo}; `aviso` é None ou texto.
    """
    valores = dict(PARAMETROS_PADRAO)
    detalhes = {}
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        for nome, info in dados["parametros"].items():
            valores[nome] = info["valor"]
            detalhes[nome] = info
        return valores, detalhes, None
    except (OSError, ValueError, KeyError, TypeError):
        return valores, detalhes, "Arquivo de parâmetros indisponível: usando valores padrão."


# ----------------------------------------------------------------------
# Cálculos (funções puras, fáceis de testar)
# ----------------------------------------------------------------------
def custo_energia(consumo_kwh, tarifa, tem_tarifa_social, limite_gratuito):
    """Valor aproximado da energia no mês (sem impostos extras e sem iluminação pública).

    Com Tarifa Social, os primeiros `limite_gratuito` kWh não são cobrados.
    """
    if tem_tarifa_social:
        kwh_cobrados = max(consumo_kwh - limite_gratuito, 0)
    else:
        kwh_cobrados = consumo_kwh
    return kwh_cobrados * tarifa


def analisar_consumo(consumos):
    """Resumo dos meses informados (do mais recente para o mais antigo)."""
    media = sum(consumos) / len(consumos)
    ultimo = consumos[0]
    return {
        "media_kwh": media,
        "ultimo_kwh": ultimo,
        "diferenca_ultimo_vs_media": ultimo - media,
        "maior_kwh": max(consumos),
        "menor_kwh": min(consumos),
    }


def alternativa_tarifa_social(media, tarifa, faixa_renda, recebe_ts, p):
    """Tarifa Social (faixa 1) ou Desconto Social (faixa 2). Retorna None se não se aplica."""
    if recebe_ts or faixa_renda == 3:
        return None
    if faixa_renda == 1:
        economia = min(media, p["limite_gratuidade_tarifa_social_kwh"]) * tarifa
        return {
            "nome": "Tarifa Social de Energia (gratuidade até 80 kWh)",
            "custo_inicial": 0.0, "economia_mensal": economia, "economia_kwh": 0.0,
            "retorno_meses": 0.0, "co2_kg_ano": 0.0,
            "viabilidade": "ALTA: é um direito, não tem custo. Falta só o Cadastro Único atualizado e a conta de luz no nome de alguém da família.",
            "obs": "Valor aproximado: impostos e iluminação pública continuam na conta. Não reduz o consumo, então não reduz CO2.",
        }
    return {
        "nome": "Desconto Social (consumo até 120 kWh)",
        "custo_inicial": 0.0, "economia_mensal": None, "economia_kwh": 0.0,
        "retorno_meses": 0.0, "co2_kg_ano": 0.0,
        "viabilidade": "ALTA: é um direito, não tem custo. Falta só o Cadastro Único atualizado e a conta de luz no nome de alguém da família.",
        "obs": "O valor do desconto não é calculado aqui: pergunte à sua distribuidora. Não reduz o consumo, então não reduz CO2.",
    }


def alternativa_eficiencia(media, tarifa, recebe_ts, lampadas, horas_lampada,
                           pessoas, minutos_banho, potencia_chuveiro, p):
    """Troca de lâmpadas por LED + banho (chave na posição verão e menos minutos)."""
    diferenca_w = p["lampada_incandescente_w"] - p["lampada_led_w"]
    kwh_led = lampadas * diferenca_w / 1000 * horas_lampada * DIAS_NO_MES
    custo_led = lampadas * p["preco_lampada_led_reais"]

    banho_atual = potencia_chuveiro / 1000 * (minutos_banho / 60) * pessoas * DIAS_NO_MES
    minutos_novos = max(minutos_banho - p["minutos_a_menos_no_banho"], 1) if minutos_banho > 1 else minutos_banho
    banho_novo = (potencia_chuveiro / 1000 * (minutos_novos / 60) * pessoas * DIAS_NO_MES
                  * (1 - p["reducao_chuveiro_posicao_verao"]))
    kwh_banho = max(banho_atual - banho_novo, 0)

    kwh_total = min(kwh_led + kwh_banho, media)
    limite = p["limite_gratuidade_tarifa_social_kwh"]
    antes = custo_energia(media, tarifa, recebe_ts, limite)
    depois = custo_energia(media - kwh_total, tarifa, recebe_ts, limite)
    economia = antes - depois

    if economia > 0 and custo_led > 0:
        retorno = custo_led / economia
    elif economia > 0:
        retorno = 0.0
    else:
        retorno = None

    if kwh_total <= 0:
        viab = "NÃO SE APLICA: nenhuma lâmpada incandescente nem banho elétrico informados."
    elif recebe_ts and economia <= 0:
        viab = "BAIXA em dinheiro: sua energia já é gratuita até 80 kWh, então economizar não reduz o valor da conta. Ainda reduz CO2."
    else:
        viab = "ALTA: custo baixo (lâmpadas LED) e o banho depende só de hábitos."
    return {
        "nome": "Eficiência energética (lâmpadas LED + banho mais econômico)",
        "custo_inicial": custo_led, "economia_mensal": economia, "economia_kwh": kwh_total,
        "retorno_meses": retorno, "co2_kg_ano": kwh_total * 12 * p["fator_emissao_kg_co2_por_kwh"],
        "viabilidade": viab,
        "obs": (f"LED: {fmt(kwh_led)} kWh/mês; banho: {fmt(kwh_banho)} kWh/mês "
                f"(chave na posição verão e {p['minutos_a_menos_no_banho']} minutos a menos)."),
        "detalhe_led_kwh": kwh_led, "detalhe_banho_kwh": kwh_banho,
    }


def alternativa_solar(media, tarifa, recebe_ts, p):
    """Energia solar fotovoltaica (fonte renovável), sistema do tamanho do consumo."""
    # kWh que realmente podem ser compensados na conta
    if recebe_ts:
        base = media - max(p["custo_disponibilidade_kwh"], p["limite_gratuidade_tarifa_social_kwh"])
    else:
        base = media - p["custo_disponibilidade_kwh"]
    if base <= 0:
        return {
            "nome": "Energia solar fotovoltaica (fonte renovável)",
            "custo_inicial": 0.0, "economia_mensal": 0.0, "economia_kwh": 0.0,
            "retorno_meses": None, "co2_kg_ano": 0.0,
            "viabilidade": "NÃO COMPENSA: seu consumo está no nível mínimo cobrado ou já é gratuito, então a geração própria não reduziria a conta.",
            "obs": "Mesmo com painéis, a distribuidora cobra um consumo mínimo (custo de disponibilidade).",
            "kwp": 0.0,
        }
    geracao_por_kwp = p["irradiacao_media_kwh_m2_dia"] * DIAS_NO_MES * p["eficiencia_sistema_solar"]
    kwp = base / geracao_por_kwp
    custo = kwp * 1000 * p["preco_sistema_solar_reais_por_wp"]
    economia = base * tarifa
    retorno = custo / economia if economia > 0 else None
    if retorno is None:
        viab = "NÃO COMPENSA: sem economia estimada."
    elif retorno > p["retorno_maximo_viavel_meses"]:
        viab = "BAIXA: retorno acima de 8 anos."
    elif custo > 5000:
        viab = "MÉDIA: o retorno é bom, mas exige um investimento inicial alto para uma família de baixa renda (considere financiamento com cuidado)."
    else:
        viab = "MÉDIA: retorno razoável, mas exige investimento inicial e telhado adequado."
    return {
        "nome": "Energia solar fotovoltaica (fonte renovável)",
        "custo_inicial": custo, "economia_mensal": economia, "economia_kwh": base,
        "retorno_meses": retorno, "co2_kg_ano": base * 12 * p["fator_emissao_kg_co2_por_kwh"],
        "viabilidade": viab,
        "obs": (f"Sistema estimado de {fmt(kwp, 2)} kWp. Não inclui as regras de cobrança da Lei 14.300, "
                "juros de financiamento nem o custo maior por watt de sistemas pequenos."),
        "kwp": kwp,
    }


def escolher_recomendacao(alternativas):
    """Escolhe a alternativa mais indicada: direito gratuito primeiro, depois menor retorno."""
    com_economia = [a for a in alternativas
                    if a["retorno_meses"] is not None
                    and (a["economia_mensal"] is None or a["economia_mensal"] > 0)]
    if not com_economia:
        return None
    gratuitas = [a for a in com_economia if a["custo_inicial"] == 0 and a["nome"].startswith(("Tarifa", "Desconto"))]
    if gratuitas:
        return gratuitas[0]
    return min(com_economia, key=lambda a: a["retorno_meses"])


def analisar(consumos, tarifa, faixa_renda, recebe_ts, lampadas, horas_lampada,
             pessoas, minutos_banho, potencia_chuveiro, p):
    """Faz a análise completa e devolve um dicionário com os resultados."""
    resumo = analisar_consumo(consumos)
    media = resumo["media_kwh"]
    limite = p["limite_gratuidade_tarifa_social_kwh"]
    resultado = {
        "resumo": resumo,
        "conta_atual": custo_energia(media, tarifa, recebe_ts, limite),
        "alternativas": [],
    }
    for alt in (
        alternativa_tarifa_social(media, tarifa, faixa_renda, recebe_ts, p),
        alternativa_eficiencia(media, tarifa, recebe_ts, lampadas, horas_lampada,
                               pessoas, minutos_banho, potencia_chuveiro, p),
        alternativa_solar(media, tarifa, recebe_ts, p),
    ):
        if alt is not None:
            resultado["alternativas"].append(alt)
    resultado["recomendada"] = escolher_recomendacao(resultado["alternativas"])
    return resultado


# ----------------------------------------------------------------------
# Tela
# ----------------------------------------------------------------------
def moeda(valor):
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mostrar_resultado(resultado, tarifa, detalhes):
    resumo = resultado["resumo"]
    print()
    print("=== Análise do seu consumo ===")
    print(f"Média dos meses informados: {fmt(resumo['media_kwh'])} kWh")
    diferenca = resumo["diferenca_ultimo_vs_media"]
    sinal = "+" if diferenca >= 0 else "-"
    print(f"Mês mais recente: {fmt(resumo['ultimo_kwh'])} kWh "
          f"({sinal}{fmt(abs(diferenca))} kWh em relação à média)")
    print(f"Maior mês: {fmt(resumo['maior_kwh'])} kWh | menor mês: {fmt(resumo['menor_kwh'])} kWh")
    print(f"Valor aproximado da energia por mês (tarifa {moeda(tarifa)}/kWh): "
          f"{moeda(resultado['conta_atual'])}")

    print()
    print("=== Comparação das alternativas (valores estimados) ===")
    for numero, alt in enumerate(resultado["alternativas"], start=1):
        print(f"{numero}) {alt['nome']}")
        print(f"   Custo inicial: {moeda(alt['custo_inicial'])}")
        if alt["economia_mensal"] is None:
            print("   Economia por mês: valor não calculado")
        elif alt["economia_kwh"] > 0:
            print(f"   Economia por mês: {moeda(alt['economia_mensal'])} "
                  f"({fmt(alt['economia_kwh'])} kWh a menos)")
        else:
            print(f"   Economia por mês: {moeda(alt['economia_mensal'])}")
        if alt["retorno_meses"] is None:
            print("   Retorno do investimento: não se aplica")
        elif alt["retorno_meses"] == 0:
            print("   Retorno do investimento: imediato (sem custo)")
        else:
            print(f"   Retorno do investimento: {fmt(alt['retorno_meses'])} meses "
                  f"(cerca de {fmt(alt['retorno_meses'] / 12)} anos)")
        print(f"   CO2 evitado: {fmt(alt['co2_kg_ano'])} kg por ano")
        print(f"   Viabilidade: {alt['viabilidade']}")
        print(f"   Observação: {alt['obs']}")
        print()

    recomendada = resultado["recomendada"]
    print("=== Sugestão ===")
    if recomendada is None:
        print("Com os dados informados, nenhuma alternativa gera economia em dinheiro. "
              "Se quiser reduzir o consumo, converse com a distribuidora ou use a orientação sobre economia de energia.")
    else:
        print(f"Pelos dados informados, a alternativa mais indicada é: {recomendada['nome']}.")
    print("O Brasil já gera boa parte da energia de fontes renováveis, por isso o CO2 evitado por kWh é baixo; "
          "o ganho principal aqui é financeiro.")
    print()
    print("Fontes e premissas usadas (arquivo data/energia_parametros.json):")
    for nome in ("limite_gratuidade_tarifa_social_kwh", "irradiacao_media_kwh_m2_dia",
                 "preco_sistema_solar_reais_por_wp", "fator_emissao_kg_co2_por_kwh"):
        info = detalhes.get(nome)
        if info:
            print(f"  - {nome}: {info['valor']} {info['unidade']} [{info['tipo']}] {info['fonte']}")
    print(f"Aviso: {AVISO_ENERGIA}")


def executar(caminho_parametros):
    """Conversa com a pessoa e mostra a análise.

    Retorna None se a pessoa voltar logo no início; caso contrário,
    retorna {"ajudou": True/False}.
    """
    valores, detalhes, aviso = carregar_parametros(caminho_parametros)
    print("\n--- Calculadora de energia ---")
    print("Use os valores da sua conta de luz. Digite 0 no primeiro valor para voltar.")
    print(f"Aviso: {AVISO_ENERGIA}")
    if aviso:
        print(f"  Atenção: {aviso}")

    consumo1 = ler_decimal("Consumo do mês mais recente, em kWh (0 para voltar): ", 0, 5000)
    if consumo1 == 0:
        return None
    consumo2 = ler_decimal("Consumo de 1 mês antes, em kWh: ", 1, 5000)
    consumo3 = ler_decimal("Consumo de 2 meses antes, em kWh: ", 1, 5000)
    tarifa = ler_decimal(
        f"Valor do kWh na sua conta, em R$ (Enter = {str(valores['tarifa_exemplo_reais_kwh']).replace('.', ',')} de exemplo): ",
        0.1, 5, padrao=valores["tarifa_exemplo_reais_kwh"])

    print("Renda por pessoa da família:")
    print("  1) Até meio salário mínimo")
    print("  2) Mais de meio e até 1 salário mínimo")
    print("  3) Mais de 1 salário mínimo")
    faixa = ler_inteiro("Escolha (1-3): ", 1, 3)
    recebe_ts = False
    if faixa == 1:
        recebe_ts = ler_sim_nao("Sua conta de luz já tem a Tarifa Social? (s/n): ")

    lampadas = ler_inteiro("Quantas lâmpadas incandescentes de 60 W existem na casa? (0 se nenhuma): ", 0, 50)
    horas = 5.0
    if lampadas > 0:
        horas = ler_decimal("Horas por dia que cada uma fica acesa (Enter = 5): ", 0.5, 24, padrao=5.0)

    pessoas = ler_inteiro("Quantas pessoas tomam banho no chuveiro elétrico por dia? (0 se não usa): ", 0, 15)
    minutos = 10
    potencia = 5500
    if pessoas > 0:
        minutos = ler_inteiro("Minutos de banho por pessoa (de 1 a 60): ", 1, 60)
        potencia = ler_inteiro("Potência do chuveiro em W (fica na etiqueta dele, de 1000 a 8000; exemplo: 5500): ", 1000, 8000)

    resultado = analisar([consumo1, consumo2, consumo3], tarifa, faixa, recebe_ts, lampadas,
                         horas, pessoas, minutos, potencia, valores)
    mostrar_resultado(resultado, tarifa, detalhes)
    ajudou = ler_sim_nao("Essa análise ajudou você? (s/n): ")
    return {"ajudou": ajudou}
