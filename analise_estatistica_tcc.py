"""TCC II — Análise estatística de métricas automáticas e avaliações humanas.
Uso: python analise_estatistica_tcc.py
Entrada: Dataset_TCC_Com_Metricas.xlsx na mesma pasta.
Saídas: Resultados_Estatisticos_TCC.xlsx e gráficos PNG em Graficos_TCC/.
"""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import scipy.stats as stats
import krippendorff
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
ENTRADA = BASE / 'Dataset_TCC_Com_Metricas.xlsx'
SAIDA = BASE / 'Resultados_Estatisticos_TCC.xlsx'
PASTA_GRAFICOS = BASE / 'Graficos_TCC'
CRITERIOS = ['coherence_1_5', 'relevance_1_5', 'fluency_1_5', 'utility_1_5']
METRICAS = ['bleu', 'rouge', 'meteor', 'bertscore', 'cosine_similarity']
ROTULOS = {'coherence_1_5': 'Coerência', 'relevance_1_5': 'Relevância',
           'fluency_1_5': 'Fluência', 'utility_1_5': 'Utilidade',
           'media_geral': 'Média geral'}

def correlacao(x, y):
    dados = pd.DataFrame({'x': x, 'y': y}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(dados) < 3 or dados.x.nunique() < 2 or dados.y.nunique() < 2:
        return float('nan'), float('nan'), len(dados)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        rho, p = stats.spearmanr(dados.x, dados.y)
    return float(rho), float(p), len(dados)

def alfa_ordinal(avaliacoes, criterio, ids):
    matriz = (avaliacoes.pivot(index='evaluator_code', columns='question_id', values=criterio)
              .reindex(index=['A1','A2','A3','A4','A5'], columns=ids))
    valores = matriz.to_numpy(dtype=float)
    return float(krippendorff.alpha(reliability_data=valores, level_of_measurement='ordinal'))

def main():
    if not ENTRADA.exists():
        raise FileNotFoundError(f'Coloque {ENTRADA.name} na mesma pasta deste script.')
    print('Lendo planilha:', ENTRADA.name, flush=True)
    perguntas = pd.read_excel(ENTRADA, sheet_name='Dataset_Perguntas')
    avaliacoes = pd.read_excel(ENTRADA, sheet_name='Avaliacoes_Humanas')
    exigidas = ['question_id', 'category', 'chatbot_response', 'reference_answer_1', 'reference_answer_2'] + METRICAS
    faltantes = [c for c in exigidas if c not in perguntas.columns]
    faltantes += [c for c in ['question_id', 'evaluator_code'] + CRITERIOS if c not in avaliacoes.columns]
    if faltantes:
        raise ValueError('Colunas ausentes: ' + ', '.join(faltantes))
    if len(perguntas) != 100 or perguntas.question_id.nunique() != 100:
        raise ValueError('Esperadas exatamente 100 perguntas com IDs únicos.')
    if len(avaliacoes) != 500 or avaliacoes[['question_id','evaluator_code']].duplicated().any():
        raise ValueError('Esperadas exatamente 500 avaliações únicas (100 perguntas × 5 avaliadores).')
    if set(avaliacoes.question_id) != set(perguntas.question_id):
        raise ValueError('Os IDs das avaliações não correspondem aos IDs das perguntas.')
    if set(avaliacoes.evaluator_code) != {'A1','A2','A3','A4','A5'}:
        raise ValueError('Os avaliadores precisam ser A1, A2, A3, A4 e A5.')
    if perguntas[exigidas].isna().any().any():
        raise ValueError('Há perguntas, referências, respostas ou métricas ausentes.')
    for c in METRICAS:
        perguntas[c] = pd.to_numeric(perguntas[c], errors='coerce')
    for c in CRITERIOS:
        avaliacoes[c] = pd.to_numeric(avaliacoes[c], errors='coerce')
    if perguntas[METRICAS].isna().any().any() or avaliacoes[CRITERIOS].isna().any().any():
        raise ValueError('Existem notas ou métricas não numéricas ou ausentes.')
    if not avaliacoes[CRITERIOS].apply(lambda s: s.between(1, 5) & (s % 1 == 0)).all().all():
        raise ValueError('As avaliações Likert devem ser inteiros de 1 a 5.')
    if not (avaliacoes.groupby('question_id').evaluator_code.nunique() == 5).all():
        raise ValueError('Cada pergunta deve ter notas dos cinco avaliadores.')

    ids = perguntas.question_id.tolist()
    avaliacoes['media_geral'] = avaliacoes[CRITERIOS].mean(axis=1)
    # A nota geral é uma média composta; seu alfa é exploratório e não substitui os alfas ordinais.
    humanas = avaliacoes.groupby('question_id')[CRITERIOS + ['media_geral']].mean().reset_index()
    base = perguntas[['question_id','category'] + METRICAS].merge(humanas, on='question_id', validate='one_to_one')
    print('Dados validados: 100 perguntas, 500 avaliações, 5 métricas.', flush=True)

    alfas = []
    for criterio in CRITERIOS:
        a = alfa_ordinal(avaliacoes, criterio, ids)
        alfas.append({'criterio': ROTULOS[criterio], 'nivel': 'ordinal', 'alfa_krippendorff': a,
                      'n_perguntas': 100, 'n_avaliadores': 5})
    # A média de 4 itens não é uma categoria Likert ordinal original; use nível intervalar.
    matriz_geral = (avaliacoes.pivot(index='evaluator_code', columns='question_id', values='media_geral')
                    .reindex(index=['A1','A2','A3','A4','A5'], columns=ids).to_numpy(dtype=float))
    alfas.append({'criterio': 'Média geral (exploratória)', 'nivel': 'interval',
                  'alfa_krippendorff': float(krippendorff.alpha(reliability_data=matriz_geral,
                                                               level_of_measurement='interval')),
                  'n_perguntas': 100, 'n_avaliadores': 5})
    df_alfas = pd.DataFrame(alfas)
    print('Alfa de Krippendorff calculado.', flush=True)

    linhas = []
    for grupo, subconjunto in [('Geral', base)] + [(f'Categoria {c}', g) for c,g in base.groupby('category', sort=True)]:
        for criterio in CRITERIOS + ['media_geral']:
            for metrica in METRICAS:
                rho, p, n = correlacao(subconjunto[metrica], subconjunto[criterio])
                linhas.append({'grupo': grupo, 'criterio': ROTULOS[criterio], 'metrica': metrica,
                               'n': n, 'spearman_rho': rho, 'p_valor': p,
                               'significativo_0_05_sem_ajuste': bool(p < 0.05) if np.isfinite(p) else False})
    df_corr = pd.DataFrame(linhas)
    df_geral = df_corr.query("grupo == 'Geral'").copy()
    resumo_avaliadores = (avaliacoes.groupby('evaluator_code')[CRITERIOS + ['media_geral']]
                          .agg(['mean', 'std']).round(4))
    resumo_avaliadores.columns = [f'{col}_{estat}' for col,estat in resumo_avaliadores.columns]
    resumo_avaliadores = resumo_avaliadores.reset_index()
    resumo_categorias = base.groupby('category')[METRICAS + CRITERIOS + ['media_geral']].agg(['mean','std'])
    resumo_categorias.columns = [f'{col}_{estat}' for col,estat in resumo_categorias.columns]
    resumo_categorias = resumo_categorias.reset_index()

    PASTA_GRAFICOS.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    ger = df_geral[df_geral.criterio == 'Média geral']
    ax.bar(ger.metrica, ger.spearman_rho)
    ax.axhline(0, color='black', linewidth=.8)
    ax.set_ylabel('Coeficiente de Spearman (rho)')
    ax.set_title('Métricas automáticas × média das avaliações humanas')
    ax.tick_params(axis='x', labelrotation=15)
    fig.tight_layout()
    fig.savefig(PASTA_GRAFICOS / '01_spearman_media_geral.png', dpi=180)
    plt.close(fig)

    matriz = df_geral.pivot(index='criterio', columns='metrica', values='spearman_rho')
    matriz = matriz.reindex(index=[ROTULOS[c] for c in CRITERIOS] + ['Média geral'], columns=METRICAS)
    fig, ax = plt.subplots(figsize=(10, 5))
    img = ax.imshow(matriz.values, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
    ax.set_xticks(range(len(METRICAS)), METRICAS, rotation=20, ha='right')
    ax.set_yticks(range(len(matriz.index)), matriz.index)
    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            valor = matriz.iat[i,j]
            ax.text(j, i, f'{valor:.2f}' if pd.notna(valor) else 'N/A', ha='center', va='center')
    ax.set_title('Spearman por critério e métrica (100 perguntas)')
    fig.colorbar(img, ax=ax, label='Spearman rho')
    fig.tight_layout()
    fig.savefig(PASTA_GRAFICOS / '02_mapa_calor_spearman.png', dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(df_alfas.criterio, df_alfas.alfa_krippendorff)
    ax.axhline(0, color='black', linewidth=.8)
    ax.set_ylabel('Alfa de Krippendorff')
    ax.set_title('Concordância entre os cinco avaliadores')
    ax.tick_params(axis='x', labelrotation=18)
    fig.tight_layout()
    fig.savefig(PASTA_GRAFICOS / '03_alfa_krippendorff.png', dpi=180)
    plt.close(fig)

    metodologia = pd.DataFrame([
        ['Unidade de análise', 'Pergunta/resposta (100 unidades)'],
        ['Notas humanas', 'Média dos cinco avaliadores por critério; média geral das quatro dimensões'],
        ['Concordância', 'Alfa de Krippendorff ordinal para cada critério Likert 1–5'],
        ['Concordância média geral', 'Alfa intervalar exploratório para média composta (não ordinal)'],
        ['Correlação', 'Spearman bicaudal, calculado com scipy.stats.spearmanr'],
        ['p-valor', 'Sem correção para testes múltiplos; resultados exploratórios'],
        ['Significância', 'p < 0,05 (sem ajuste); não implica causalidade'],
        ['Referências automáticas', 'Métricas importadas da planilha original; não recalculadas'],
        ['Categorias', '20 perguntas por categoria; análises por categoria exploratórias'],
        ['Observação', 'Concordância e correlação avaliam propriedades diferentes'],
    ], columns=['Item', 'Descrição'])

    with pd.ExcelWriter(SAIDA, engine='openpyxl') as writer:
        df_alfas.to_excel(writer, sheet_name='Krippendorff', index=False)
        df_geral.to_excel(writer, sheet_name='Spearman_Geral', index=False)
        df_corr[df_corr.grupo != 'Geral'].to_excel(writer, sheet_name='Spearman_Categorias', index=False)
        resumo_avaliadores.to_excel(writer, sheet_name='Resumo_Avaliadores', index=False)
        resumo_categorias.to_excel(writer, sheet_name='Resumo_Categorias', index=False)
        base.to_excel(writer, sheet_name='Base_Analise', index=False)
        metodologia.to_excel(writer, sheet_name='Metodologia', index=False)
        for ws in writer.book.worksheets:
            ws.freeze_panes = 'A2'
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                from openpyxl.styles import Font, PatternFill
                cell.font = Font(bold=True, color='FFFFFF')
                cell.fill = PatternFill('solid', fgColor='17365D')
            for col in ws.columns:
                letter = col[0].column_letter
                largura = min(55, max(14, max(len(str(c.value or '')) for c in list(col)[:100]) + 2))
                ws.column_dimensions[letter].width = largura
    print('CONCLUÍDO:', SAIDA.name, flush=True)
    print('Gráficos salvos em:', PASTA_GRAFICOS, flush=True)
    print('\nAlfa de Krippendorff:')
    print(df_alfas[['criterio','alfa_krippendorff']].to_string(index=False, float_format=lambda x: f'{x:.4f}'))
    print('\nSpearman × média geral:')
    print(ger[['metrica','spearman_rho','p_valor']].to_string(index=False, float_format=lambda x: f'{x:.4f}'))

if __name__ == '__main__':
    main()
