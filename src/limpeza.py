"""Funcoes de limpeza que servem a qualquer fonte.

Regra do modulo: nenhuma funcao daqui menciona o nome de uma fonte.
O que e especifico de uma fonte fica no script dela.
"""
import json

import pandas as pd


def _colunas_texto(df):
    return [c for c in df.columns if pd.api.types.is_string_dtype(df[c])]


def contar_com_espaco(df):
    """Quantas celulas de cada coluna de texto tem espaco sobrando (pontas ou repetido)."""
    contagem = {}
    for c in _colunas_texto(df):
        s = df[c].dropna()
        limpo = s.str.strip().str.replace(r"\s+", " ", regex=True)
        n = int((s != limpo).sum())
        if n:
            contagem[c] = n
    return contagem


def tirar_espacos(df):
    """Tira espaco nas pontas e repetido no meio, dos nomes de coluna e do conteudo.

    O str.strip tambem remove o espaco 'nao separavel' (\\xa0), que nao se ve.
    """
    df.columns = df.columns.str.strip()
    for c in _colunas_texto(df):
        df[c] = df[c].str.strip().str.replace(r"\s+", " ", regex=True)
    return df


def chave_texto(serie):
    """Versao comparavel de um texto: sem acento, sem espaco sobrando, minuscula.

    Serve para comparar e juntar, nao para exibir: o rotulo original fica na tabela.
    """
    s = serie.astype("string").str.strip().str.lower()
    s = s.str.replace(r"\s+", " ", regex=True)
    s = s.str.normalize("NFKD")
    s = s.str.encode("ascii", errors="ignore").str.decode("utf-8")
    return s


def aplicar_mapa(serie, mapa):
    """Troca variantes pelo valor canonico. O que nao estiver no mapa fica como esta."""
    return serie.replace(mapa)


def conferir_chave(df, chave):
    """Mostra e remove linhas repetidas pela chave (uma coluna ou lista de colunas)."""
    repetidas = int(df.duplicated(subset=chave).sum())
    print("chaves repetidas:", repetidas)
    if repetidas:
        print(df[df.duplicated(subset=chave, keep=False)])
    return df.drop_duplicates(subset=chave), repetidas


def limites_iqr(serie):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def marcar_extremos(df, coluna):
    """Cria <coluna>_extremo (True fora dos limites do IQR). Marca, nao remove."""
    baixo, alto = limites_iqr(df[coluna])
    df[coluna + "_extremo"] = (df[coluna] < baixo) | (df[coluna] > alto)
    print(f"{coluna}: IQR em [{baixo:.1f}; {alto:.1f}] -> {int(df[coluna + '_extremo'].sum())} marcados")
    return df


def contar_zscore(df, coluna, limite=3):
    """Quantos valores tem |z| acima do limite. Serve so para comparar com o IQR."""
    z = (df[coluna] - df[coluna].mean()) / df[coluna].std()
    n = int((z.abs() > limite).sum())
    print(f"{coluna}: |z| > {limite} -> {n} marcados")
    return n


def remover_erros(df, coluna, minimo, maximo):
    """Remove so o que o dominio prova ser erro (faixa vem do assunto, nao da estatistica)."""
    valido = df[coluna].between(minimo, maximo)
    removidas = int((~valido).sum())
    print(f"{coluna} fora de [{minimo}; {maximo}] removidas:", removidas)
    return df[valido].copy(), removidas


def acrescentar_jsonl(caminho, info):
    """Acrescenta uma linha ao registro de proveniencia, sem apagar as anteriores."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")
