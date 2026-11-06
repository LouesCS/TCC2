"""Calcula BLEU, ROUGE-L, METEOR, BERTScore e Sentence-BERT para o TCC.

Uso: python calcular_metricas_tcc.py
Entrada: Dataset_TCC_Final_100_Respostas_5_Avaliadores.xlsx
Saída: Dataset_TCC_Com_Metricas.xlsx

Política de múltiplas referências:
- BLEU-4: duas referências simultâneas, com smoothing method1.
- ROUGE-L F1, METEOR, BERTScore F1 e Sentence-BERT cosseno: maior
  pontuação obtida entre as duas referências.
- Tokenização lexical: regex Unicode de palavras e números, em minúsculas.
- METEOR: WordNet padrão do NLTK (em inglês); para português, interpretar
  como alinhamento lexical aproximado, sem assumir sinonímia em português.
"""
from pathlib import Path
import re
import sys
import numpy as np
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score
from rouge_score import rouge_scorer
from bert_score import score as bert_score
from sentence_transformers import SentenceTransformer
from openpyxl import load_workbook

BASE = Path(__file__).resolve().parent
INPUT = BASE / 'Dataset_TCC_Final_100_Respostas_5_Avaliadores.xlsx'
OUTPUT = BASE / 'Dataset_TCC_Com_Metricas.xlsx'
BERT_MODEL = 'bert-base-multilingual-cased'
SBERT_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'


def tokens(text):
    return re.findall(r'\w+', text.lower(), flags=re.UNICODE)


def main():
    if not INPUT.exists():
        sys.exit(f'ERRO: Planilha não encontrada: {INPUT.name}')
    print('Lendo planilha...')
    wb = load_workbook(INPUT)
    sheet = wb['Dataset_Perguntas']
    rows = list(sheet.iter_rows(min_row=2, max_row=101, min_col=1, max_col=7, values_only=True))
    if len(rows) != 100:
        sys.exit('ERRO: esperado um conjunto de 100 perguntas.')
    ids = [str(r[0]).strip() for r in rows]
    if len(set(ids)) != 100:
        sys.exit('ERRO: IDs duplicados.')
    for i, r in enumerate(rows, start=2):
        if any(not isinstance(r[c], str) or not r[c].strip() for c in (4, 5, 6)):
            sys.exit(f'ERRO: referência ou resposta vazia na linha {i}, ID {r[0]}.')

    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
    rouge_scorer_obj = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=False)
    smooth = SmoothingFunction().method1
    lexical = []
    for i, row in enumerate(rows, start=1):
        ref1, ref2, answer = row[4], row[5], row[6]
        ref_tokens = [tokens(ref1), tokens(ref2)]
        answer_tokens = tokens(answer)
        bleu = sentence_bleu(ref_tokens, answer_tokens,
                             weights=(.25, .25, .25, .25), smoothing_function=smooth)
        rouge = max(rouge_scorer_obj.score(ref, answer)['rougeL'].fmeasure
                    for ref in (ref1, ref2))
        meteor = max(meteor_score([ref_tok], answer_tokens) for ref_tok in ref_tokens)
        lexical.append((float(bleu), float(rouge), float(meteor)))
        if i % 20 == 0:
            print(f'Métricas lexicais: {i}/100')

    answers = [r[6] for r in rows]
    references = [r[4] for r in rows] + [r[5] for r in rows]
    candidates = answers + answers
    print('Calculando BERTScore (primeira execução pode baixar o modelo)...')
    _, _, f1 = bert_score(candidates, references, model_type=BERT_MODEL,
                          lang='pt', batch_size=8, verbose=True, device='cpu')
    f1_values = f1.detach().cpu().numpy()
    bert = np.maximum(f1_values[:100], f1_values[100:])

    print('Calculando Sentence-BERT...')
    model = SentenceTransformer(SBERT_MODEL, device='cpu')
    vectors = model.encode(answers + references, batch_size=16,
                           normalize_embeddings=True, show_progress_bar=True)
    answer_vec = vectors[:100]
    ref1_vec = vectors[100:200]
    ref2_vec = vectors[200:300]
    cosine = np.maximum(np.sum(answer_vec * ref1_vec, axis=1),
                        np.sum(answer_vec * ref2_vec, axis=1))

    output_rows = [[round(lexical[i][0], 6), round(lexical[i][1], 6),
                    round(lexical[i][2], 6), round(float(bert[i]), 6),
                    round(float(cosine[i]), 6)] for i in range(100)]
    for row_idx, values in enumerate(output_rows, start=2):
        for col_idx, value in enumerate(values, start=8):
            sheet.cell(row=row_idx, column=col_idx, value=value)
    wb.save(OUTPUT)
    print(f'CONCLUÍDO: {OUTPUT.name}')
    print('100 perguntas, cinco métricas por pergunta. Avaliações humanas preservadas.')
    print('Modelos:', BERT_MODEL, '|', SBERT_MODEL)


if __name__ == '__main__':
    main()
