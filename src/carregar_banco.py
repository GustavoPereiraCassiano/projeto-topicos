"""Carga da prata em um banco SQLite (opcional; usa so a biblioteca padrao + pandas).

Le os Parquet de dados/prata e grava as tabelas em dados/prata/brasileirao.db.
Cada execucao recria as tabelas: a prata e reconstruivel.
"""
import sqlite3
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PRATA = RAIZ / "dados" / "prata"
BANCO = PRATA / "brasileirao.db"
TABELAS = {"partidas": "partidas.parquet", "clubes": "clubes.parquet", "ufs": "ufs.parquet"}


def preparar(df):
    """SQLite nao tem categoria: converte para texto. Data vira texto ISO."""
    df = df.copy()
    for coluna in df.columns:
        if isinstance(df[coluna].dtype, pd.CategoricalDtype):
            df[coluna] = df[coluna].astype("string")
        elif pd.api.types.is_datetime64_any_dtype(df[coluna]):
            df[coluna] = df[coluna].dt.strftime("%Y-%m-%d")
    return df


def main():
    with sqlite3.connect(BANCO) as con:
        for tabela, arquivo in TABELAS.items():
            caminho = PRATA / arquivo
            if not caminho.exists():
                raise FileNotFoundError(f"falta {caminho}; rode a transformacao antes")
            df = preparar(pd.read_parquet(caminho))
            df.to_sql(tabela, con, if_exists="replace", index=False)
            print(f"{tabela}: {len(df)} linhas")
    print("banco em:", BANCO)


if __name__ == "__main__":
    main()
