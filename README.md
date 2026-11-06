
# Avaliação Híbrida da Qualidade de Respostas de Chatbots

Este repositório reúne os códigos Python utilizados no desenvolvimento do TCC II para calcular métricas automáticas de avaliação textual e analisar a relação dessas métricas com avaliações humanas.

O experimento considera 100 perguntas, duas respostas de referência por pergunta e respostas produzidas por um chatbot. As respostas foram avaliadas por cinco avaliadores, utilizando quatro critérios em escala Likert de 1 a 5: coerência, relevância, fluência e utilidade.

## Objetivo

Disponibilizar os scripts utilizados para:

- Calcular métricas automáticas de similaridade entre as respostas do chatbot e as respostas de referência.
- Analisar a concordância entre os avaliadores por meio do alfa de Krippendorff.
- Calcular a correlação de Spearman entre as métricas automáticas e as avaliações humanas.
- Exportar os resultados em planilhas e gráficos para apoiar a análise dos dados.

## Métricas e métodos utilizados

O projeto utiliza cinco métricas automáticas:

- **BLEU-4:** compara a sobreposição de sequências de palavras entre a resposta gerada e as referências.
- **ROUGE-L F1:** avalia a maior subsequência comum entre a resposta e cada referência.
- **METEOR:** calcula a correspondência lexical entre a resposta e as referências.
- **BERTScore F1:** compara representações contextuais dos textos usando o modelo `bert-base-multilingual-cased`.
- **Similaridade de cosseno com Sentence-BERT:** compara embeddings gerados pelo modelo `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.

Para ROUGE-L, METEOR, BERTScore e Sentence-BERT, o código considera a maior pontuação obtida entre as duas referências. O BLEU-4 utiliza as duas referências simultaneamente.

Na análise estatística, são utilizados:

- **Alfa de Krippendorff ordinal:** para avaliar a concordância dos cinco avaliadores em cada critério Likert.
- **Correlação de Spearman:** para verificar a associação entre cada métrica automática e as avaliações humanas.

## Estrutura dos arquivos

Organize os arquivos da seguinte forma:

```text
TCC_Chatbots/
│
├── calcular_metricas_tcc.py
├── analise_estatistica_tcc.py
├── Dataset_TCC_Final_100_Respostas_5_Avaliadores.xlsx
├── requirements.txt
└── README.md
```

### Descrição dos arquivos

| Arquivo | Descrição |
|---|---|
| `calcular_metricas_tcc.py` | Calcula as cinco métricas automáticas. |
| `analise_estatistica_tcc.py` | Realiza as análises estatísticas e gera gráficos. |
| `Dataset_TCC_Final_100_Respostas_5_Avaliadores.xlsx` | Planilha de entrada com perguntas, referências, respostas e avaliações humanas. |
| `requirements.txt` | Lista as bibliotecas necessárias para executar os scripts. |

## Requisitos

- Python 3.10 ou superior.
- Conexão com a internet na primeira execução para instalação de dependências e download dos recursos e modelos necessários.
- Espaço em disco para os modelos utilizados pelo BERTScore e Sentence-BERT.

## Instalação

Primeiro, clone o repositório:

```bash
git clone URL_DO_REPOSITORIO
cd NOME_DO_REPOSITORIO
```

Crie um ambiente virtual:

**Windows:**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Como executar

### 1. Calcular as métricas automáticas

Coloque a planilha `Dataset_TCC_Final_100_Respostas_5_Avaliadores.xlsx` na mesma pasta do script e execute:

```bash
python calcular_metricas_tcc.py
```

O script calcula as cinco métricas para as 100 respostas e gera:

```text
Dataset_TCC_Com_Metricas.xlsx
```

A planilha de saída mantém os dados existentes e acrescenta as colunas das métricas calculadas.

### 2. Executar a análise estatística

Após executar o primeiro script, mantenha o arquivo `Dataset_TCC_Com_Metricas.xlsx` na mesma pasta do segundo script e execute:

```bash
python analise_estatistica_tcc.py
```

O script gera:

```text
Resultados_Estatisticos_TCC.xlsx
```

Também é criada a pasta `Graficos_TCC`, contendo:

- `01_spearman_media_geral.png`
- `02_mapa_calor_spearman.png`
- `03_alfa_krippendorff.png`

A planilha estatística contém as seguintes abas:

- Krippendorff;
- Spearman_Geral;
- Spearman_Categorias;
- Resumo_Avaliadores;
- Resumo_Categorias;
- Base_Analise;
- Metodologia.

## Organização do experimento

O conjunto de dados utilizado no estudo possui:

- 100 perguntas divididas em cinco categorias;
- Duas respostas de referência para cada pergunta;
- 100 respostas geradas pelo chatbot;
- Cinco avaliadores identificados como A1, A2, A3, A4 e A5;
- Quatro critérios de avaliação humana;
- Escala Likert de 1 a 5;
- 500 registros de avaliação humana.

## Observações metodológicas

- A unidade de análise das correlações é a pergunta, totalizando 100 unidades.
- As notas dos cinco avaliadores são agregadas por pergunta e critério antes das correlações.
- O alfa de Krippendorff é calculado no nível ordinal para cada critério Likert.
- O alfa da média geral composta é apresentado separadamente como análise exploratória intervalar.
- Os testes de Spearman por categoria são exploratórios e os p-valores gerados pelo script não possuem correção para testes múltiplos.
- O METEOR utiliza os recursos WordNet do NLTK. Como o WordNet padrão é predominantemente em inglês, os resultados dessa métrica para textos em português devem ser interpretados considerando essa limitação.
- Os scripts não fazem chamadas à API do ChatGPT. As respostas do chatbot foram coletadas previamente pela interface conversacional e inseridas na planilha do experimento.

## Reprodutibilidade

Para reproduzir o processamento, execute os scripts nesta ordem:

1. `calcular_metricas_tcc.py`
2. `analise_estatistica_tcc.py`

Utilize a mesma planilha de entrada e as mesmas versões das bibliotecas e dos modelos para facilitar a comparação dos resultados.

## Licença

Este repositório não define uma licença de uso. Para permitir formalmente a reutilização, modificação e distribuição do código, escolha e inclua uma licença antes da publicação.
