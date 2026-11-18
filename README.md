# Citizen Assist AI

Assistente de orientação ao cidadão, executado no terminal, para **famílias de baixa renda**.
Global Solution 2026.2 | CitizenTech | FIAP, 1º ano de Ciência da Computação.
Disciplinas: **Pensamento Computacional e Automação com Python** e **Soluções em Energias Renováveis e Sustentáveis**.

## Integrantes

| Nome | RM |
|---|---|
| Henrique Eduardo da Silveira | 571803 |
| Felipe Elze da Silva | 572024 |

Equipe: dupla.

## Links

<!-- LINKS-INICIO -->
- Repositório GitHub: (será preenchido por `ferramentas/finalizar_readme.py`)
- Vídeo técnico do PCP (YouTube, não listado): (será preenchido por `ferramentas/finalizar_readme.py`)
- Vídeo pitch do SERS (YouTube, não listado): (será preenchido por `ferramentas/finalizar_readme.py`)
<!-- LINKS-FIM -->

## Público e problema escolhidos

**Público:** famílias de baixa renda, que são a maioria de quem depende do SUS, do Cadastro Único e dos benefícios do governo.

**Problema:** a informação existe, mas está espalhada, em linguagem técnica e misturada com páginas que parecem oficiais e não são. Uma família perde tempo (e às vezes dinheiro) para descobrir onde tirar um documento, como pegar remédio gratuito, se tem direito à Tarifa Social de energia ou o que fazer quando uma compra dá errado.

**Solução:** um assistente que responde **só com o que está na base de conhecimento verificada**, mostra a fonte oficial, a data de conferência e o aviso de que **não é canal oficial**, e **não coleta dados pessoais**.

## ODS relacionados

- **ODS 1** (Erradicação da pobreza): acesso a benefícios e programas sociais.
- **ODS 3** (Saúde e bem-estar): Cartão SUS, vacinação e Farmácia Popular.
- **ODS 7** (Energia limpa e acessível): Tarifa Social, economia de energia e energia solar.
- **ODS 10** (Redução das desigualdades): informação clara para quem tem menos acesso.
- **ODS 12** (Consumo e produção responsáveis): eficiência energética e direitos do consumidor.
- **ODS 16** (Instituições eficazes): acesso à informação confiável.

## Como executar

Requisitos: Python 3.8 ou superior. **Não usa bibliotecas externas.**

```
python main.py
```

Em alguns computadores o comando é `python3 main.py`. O programa funciona sem nenhuma instalação.

Menu:

1. **Perguntar (texto livre):** busca por pontuação na base de conhecimento.
2. **Navegar por categorias:** categorias e orientações numeradas, com **0 para voltar** em todas as telas.
3. **Calculadora de energia:** módulo do SERS (economia de energia e energia solar).
4. **Ver indicadores** e 5. **Exportar atendimentos para CSV**.
0. **Sair:** pede a nota de facilidade de uso (1 a 5).

### Exemplo de execução

```
Digite sua dúvida (0 para voltar): Como faço o cartão do SUS?

Confiança da resposta: ALTA (7 pontos)

>> Ver ou tirar o Cartão Nacional de Saúde (Cartão SUS)  [Saúde]
Hoje o Cartão Nacional de Saúde (Cartão SUS) é ligado ao CPF. Você pode ver e baixar o cartão
digital no aplicativo ou site Meu SUS Digital, entrando com a conta gov.br. ...
Documentos necessários:
  - Documento com foto
  - CPF
  - Comprovante de residência
Onde: Qualquer UBS, Secretaria Municipal de Saúde ou aplicativo Meu SUS Digital.
Fonte: https://www.gov.br/saude/pt-br/acesso-a-informacao/acoes-e-programas/cns (verificado em 2026-11-16)
Aviso: este assistente NÃO é um canal oficial.

Essa orientação respondeu sua dúvida? (s/n): s

Digite sua dúvida (0 para voltar): meu cpf é 123.456.789-00
Atenção: não digite CPF, telefone ou e-mail. Reescreva.
```

## Organização do código

| Arquivo | O que faz |
|---|---|
| `main.py` | Menu principal. Cria `BaseConhecimento` e `Assistente` e liga tudo |
| `orientacao.py` | Classe `Orientacao`: um registro do JSON, com `exibir()` |
| `base_conhecimento.py` | Classe `BaseConhecimento`: `carregar()`, `categorias()`, `por_categoria()`, `pontuar()`, `buscar()` |
| `assistente.py` | Classe `Assistente`: `perguntar()`, `navegar()`, `registrar()`, `indicadores()`, `exportar_csv()` |
| `energia.py` | Módulo de energia (SERS): análise de consumo e comparação de alternativas |
| `entrada.py` | Leitura e validação de entradas e bloqueio de dados pessoais |
| `data/base_conhecimento.json` | 18 orientações, 5 categorias, com fonte oficial e data de verificação |
| `data/energia_parametros.json` | Valores, fontes e tipo (oficial ou estimativa) usados nos cálculos de energia |
| `data/historico.json` | Atendimentos registrados |
| `data/atendimentos.csv` | Atendimentos exportados com `csv.DictWriter` |
| `ferramentas/` | Testes automáticos, verificador de links e gerador dos resultados do README |

**Composição (como na Aula 10):**

```
Assistente
└── base: BaseConhecimento
     └── orientacoes: [Orientacao, Orientacao, Orientacao, ...]
```

## Regra de pontuação usada

A pergunta é normalizada (minúsculas, sem acentos e sem pontuação) e comparada com cada orientação:

| Regra | Pontos |
|---|---|
| Palavra-chave da orientação aparece na pergunta (como palavra inteira) | +3 cada |
| Palavra da pergunta (4 letras ou mais) aparece no título | +1 cada |
| Melhor orientação com 6 pontos ou mais | Confiança **ALTA** |
| Melhor orientação com 3 a 5 pontos | Confiança **MÉDIA** |
| Nenhuma orientação com 3 pontos | "Não encontrei": sugere outras palavras e as categorias |

`buscar()` devolve uma **lista de tuplas** `(pontos, orientacao)`, da maior para a menor pontuação. O assistente mostra a melhor orientação e até duas alternativas.

**Ajustes que fizemos em relação ao exemplo do enunciado** (explicados também no vídeo):

1. **Palavras comuns ignoradas no título** (como, para, fazer, quero, preciso, onde...). Sem isso, a palavra "fazer" dava +1 ponto para quase todas as orientações.
2. **Palavra-chave só vale como palavra inteira.** A normalização coloca espaço no começo e no fim do texto, então "sus" não dispara dentro de "sustentável".
3. **Alternativas só aparecem com 3 pontos ou mais**, para não sugerir orientações sem relação.

Exemplo real: "Como faço o cartão do SUS?" → palavra-chave "cartao do sus" (+3), "sus" (+3) e "cartao" no título (+1) = **7 pontos, ALTA**.

## Dados pessoais e transparência

- O assistente **nunca pede** nome, CPF, telefone ou e-mail.
- Pergunta com **8 ou mais dígitos** ou com **@** é recusada e **não é registrada**.
- Toda resposta mostra **fonte, data de verificação e o aviso** "este assistente NÃO é um canal oficial".
- Arquivo JSON ausente ou corrompido **não trava o programa** (mensagem de aviso e continuação).

## Módulo de energia (SERS)

A opção 3 do menu analisa a **conta de luz** da família: a pessoa informa o consumo de 3 meses (kWh), o valor do kWh, a faixa de renda e alguns hábitos (lâmpadas incandescentes e banho). O assistente:

1. **Analisa o consumo** (média, último mês e comparação com os 80 kWh gratuitos da Tarifa Social).
2. **Compara 3 alternativas**, uma delas de **fonte renovável**:
   - **Tarifa Social / Desconto Social** (um direito, sem custo);
   - **Eficiência energética** (lâmpadas LED e banho mais econômico);
   - **Energia solar fotovoltaica** (renovável).
3. **Justifica com custo, retorno do investimento, viabilidade e impacto ambiental (CO2 evitado)** e sugere a mais indicada.

Linguagem simples, com fontes e avisos de limitação. Os cálculos ficam em funções puras (`analisar()` em `energia.py`) e são testados automaticamente.

**Principais fórmulas:**

- Economia de lâmpadas = lâmpadas × (60 W − 9 W) ÷ 1000 × horas por dia × 30.
- Consumo do banho = potência (kW) × minutos ÷ 60 × pessoas × 30.
- Tamanho solar (kWp) = (consumo médio − 30 kWh mínimos) ÷ (irradiação × 30 × eficiência).
- Custo solar = kWp × 1000 × preço por watt-pico. Retorno = custo ÷ economia mensal.
- CO2 evitado por ano = kWh economizados por mês × 12 × 0,0385 kg/kWh.

**Fontes e premissas** (todas em `data/energia_parametros.json`, com tipo *oficial* ou *estimativa*):

- Gratuidade de 80 kWh da Tarifa Social: ANEEL. Desconto Social (120 kWh): Lei 15.235/2025.
- Lâmpada LED de 9 W equivale à incandescente de 60 W: cartilha do Inmetro.
- Chuveiro na posição verão economiza até 30%: Cemig (citado pela Agência Minas).
- Irradiação solar: Atlas Brasileiro de Energia Solar (INPE). Usamos 4,5 kWh/m² por dia, o valor mais conservador.
- Preço do sistema solar: estudo da Greener, 1º semestre de 2026 (R$ 2,84 por Wp).
- Fator de emissão: MCTI, média do SIN em 2023 (38,5 kg de CO2 por MWh).
- Tarifa de exemplo (R$ 0,90/kWh) e preço da lâmpada LED (R$ 10) são **estimativas**: use o valor da sua conta.

## Fontes consultadas

<!-- FONTES-INICIO -->
| ID | Orientação | Fonte oficial | Verificado em |
|---|---|---|---|
| 1 | Fazer ou atualizar o Cadastro Único (CadÚnico) | https://www.gov.br/mds/pt-br/acoes-e-programas/cadastro-unico/novo-cadastro-unico | 2026-11-16 |
| 2 | Tirar ou regularizar o CPF | https://www.gov.br/pt-br/servicos/inscrever-no-cpf | 2026-11-16 |
| 3 | Tirar a Carteira de Identidade Nacional (novo RG) | https://www.gov.br/governodigital/pt-br/identidade/identificacao-do-cidadao-e-carteira-de-identidade-nacional/duvidas-frequentes-sobre-a-cin-campanha | 2026-11-16 |
| 4 | Ver ou tirar o Cartão Nacional de Saúde (Cartão SUS) | https://www.gov.br/saude/pt-br/acesso-a-informacao/acoes-e-programas/cns | 2026-11-16 |
| 5 | Ver a carteira de vacinação digital | https://meususdigital.saude.gov.br | 2026-11-16 |
| 6 | Pegar remédios gratuitos no Farmácia Popular | https://www.gov.br/saude/pt-br/assuntos/noticias/2024/julho/saiba-como-retirar-medicamentos-e-outros-itens-pelo-farmacia-popular | 2026-11-16 |
| 7 | Bolsa Família: quem tem direito e como receber | https://www.gov.br/mds/pt-br/acoes-e-programas/bolsa-familia | 2026-11-16 |
| 8 | BPC: benefício de um salário mínimo para idosos e pessoas com deficiência | https://www.gov.br/inss/pt-br/assuntos/idosos-com-mais-de-65-amnos-de-idade-e-pessoas-com-deficiencia-tem-direito-ao-bpc | 2026-11-16 |
| 9 | Gás do Povo: vale para o botijão de gás de cozinha | https://www.gov.br/mds/pt-br/acoes-e-programas/gas-do-povo/informes/informe-gas-do-povo-no01 | 2026-11-16 |
| 10 | Tarifa Social: conta de luz gratuita até 80 kWh | https://www.gov.br/aneel/pt-br/assuntos/noticias/2025/aneel-regulamenta-gratuidade-de-80-kwh-mensais-para-17-milhoes-de-familias-que-recebem-tarifa-social | 2026-11-16 |
| 11 | Desconto Social na conta de luz | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15235.htm | 2026-11-16 |
| 12 | Bandeiras tarifárias: por que a conta de luz pode ficar mais cara | https://www.gov.br/aneel/pt-br/assuntos/tarifas/bandeiras-tarifarias | 2026-11-16 |
| 13 | Reclamar da distribuidora de energia ou da conta de luz | https://goias.gov.br/agr/perguntas-frequentes-energia-eletrica/ | 2026-11-16 |
| 14 | Aparelho queimou por problema na rede elétrica | https://procon.campinas.sp.gov.br/sites/procon.campinas.sp.gov.br/files/arquivos-pesquisa/cartilha_danos_el%C3%A9tricos2-2-11.pdf | 2026-11-16 |
| 15 | Economizar energia: lâmpada LED, selo Procel e etiqueta ENCE | https://www.gov.br/inmetro/pt-br/centrais-de-conteudo/publicacoes/cartilhas/lampadaled.pdf | 2026-11-16 |
| 16 | Energia solar em casa (geração distribuída) | https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14300.htm | 2026-11-16 |
| 17 | Reclamar de uma empresa pelo Consumidor.gov.br | https://www.consumidor.gov.br | 2026-11-16 |
| 18 | Desistir de uma compra feita fora da loja (direito de arrependimento) | https://www.gov.br/mj/pt-br/assuntos/noticias/nas-relacoes-de-consumo-o-direito-de-arrependimento-e-garantido-por-lei | 2026-11-16 |
<!-- FONTES-FIM -->

## Resultado do teste com usuários

<!-- RESULTADO-INICIO -->
Os testes com usuários ainda não foram registrados. Depois dos testes, rode `python ferramentas/finalizar_readme.py` para preencher esta seção com os números reais.
<!-- RESULTADO-FIM -->

**Como o teste foi feito:** 3 ou mais pessoas de fora da equipe usaram o assistente, uma sessão por pessoa, somando 10 atendimentos ou mais. Nenhum nome ou dado pessoal foi registrado. As simulações de energia (SERS) também contam como atendimentos e ficam no mesmo `historico.json`.

## Testes automáticos

```
python ferramentas/testes_automatizados.py
```

35 testes cobrem normalização, pontuação, confiança, dados pessoais, entradas inválidas, arquivos ausentes ou corrompidos, histórico, indicadores, CSV e os cálculos do módulo de energia.

## Limitações

- A base tem **18 orientações**: o assistente só responde sobre esses assuntos e **não inventa** respostas.
- A busca por palavras-chave **não entende sinônimos** que não estejam na lista de palavras-chave. Quando algo não é encontrado, o assistente diz que não encontrou.
- Regras e valores de benefícios **mudam** (por exemplo, bandeiras tarifárias e o Gás do Povo). Cada orientação mostra a data da última conferência e deve ser revisada.
- Os cálculos de energia são **estimativas educativas**: não incluem impostos, financiamento nem as regras de cobrança da Lei 14.300, e o preço da energia solar varia por região e tamanho do sistema.
- O texto digitado nas perguntas é salvo no histórico: por isso o assistente pede que ninguém digite dados pessoais e bloqueia os casos mais comuns (CPF, telefone, e-mail), mas **não detecta nomes**.
- O assistente **não é um canal oficial** e não substitui o atendimento do governo.
- Roda no terminal, para uma pessoa por vez.

## Integração com outras disciplinas

O módulo de energia (`energia.py`) integra **Soluções em Energias Renováveis e Sustentáveis** ao mesmo assistente de **Pensamento Computacional e Automação com Python**: usa as mesmas classes de histórico, indicadores e CSV. A busca por pontuação (obrigatória em PCP) continua sendo o núcleo do atendimento.
