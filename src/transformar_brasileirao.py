import json
from datetime import datetime
from pathlib import Path

import pandas as pd

BRONZE = Path("dados/bronze/brasileirao")
PRATA = Path("dados/prata/brasileirao")
PADRAO = "*.csv"


def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))

    if not arquivos:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {BRONZE}")

    caminho = arquivos[-1]
    df = pd.read_csv(caminho)

    print("Arquivo lido:", caminho.name)
    print("Dimensões:", df.shape)

    print("\nColunas:")
    print(df.columns.tolist())

    print("\nValores ausentes:")
    print(df.isna().sum())

    return df, caminho


def tirar_espacos(df):
    df.columns = df.columns.str.strip()

    for coluna in df.select_dtypes(include="object"):
        df[coluna] = df[coluna].str.strip()

    return df


def conferir_duplicados(df):
    repetidas = df.duplicated().sum()
    print("Linhas duplicadas:", repetidas)

    return df.drop_duplicates().copy()


def converter_placares(df):
    for coluna in ["mandante_Placar", "visitante_Placar"]:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(
                df[coluna], errors="coerce"
            )

    return df


def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)

    destino = PRATA / "brasileirao.parquet"
    df.to_parquet(destino, index=False)

    print("\nArquivo salvo:", destino)
    print("Dimensões finais:", df.shape)

    return destino


def registrar(origem, destino, antes, depois, decisoes):
    info = {
        "origem": origem.name,
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": decisoes,
        "transformado_em": datetime.now().isoformat(
            timespec="seconds"
        ),
    }

    caminho = PRATA / "proveniencia.jsonl"

    with caminho.open("a", encoding="utf-8") as arquivo:
        arquivo.write(
            json.dumps(info, ensure_ascii=False) + "\n"
        )


def main():
    df, origem = carregar()
    antes = len(df)

    df = tirar_espacos(df)
    df = conferir_duplicados(df)
    df = converter_placares(df)

    destino = salvar(df)

    registrar(
        origem,
        destino,
        antes,
        len(df),
        [
            "Espacos removidos",
            "Linhas duplicadas verificadas e removidas",
            "Placar convertido para numero",
        ],
    )


if __name__ == "__main__":
    main()
