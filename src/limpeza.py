
import pandas as pd


def tirar_espacos(df):
    df.columns = df.columns.str.strip()

    for coluna in df.select_dtypes(include="object"):
        df[coluna] = df[coluna].str.strip()

    return df


def chave_texto(serie):
    return (
        serie.astype("string")
        .str.strip()
        .str.lower()
    )
