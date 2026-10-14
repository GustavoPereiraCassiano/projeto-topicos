import json
from datetime import datetime
from pathlib import Path

import pandas as pd

BRONZE = Path("dados/bronze/ibge")
PRATA = Path("dados/prata/ibge")
PADRAO = "*.csv"

def carregar():
    arquivos = sorted(BRONZE.glob("*.json"))

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum JSON encontrado em {BRONZE}"
        )

    caminho = arquivos[-1]
    df = pd.read_json(caminho)

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
        df[coluna] = df[coluna].apply(
            lambda valor: valor.strip()
            if isinstance(valor, str)
            else valor
        )

    return df


def conferir_chave(df, chave="id"):
    if chave not in df.columns:
        print(f"Atenção: coluna '{chave}' não encontrada.")
        return df

    repetidas = df[chave].duplicated().sum()
    print("Chaves repetidas:", repetidas)

    if repetidas:
        print(df[df[chave].duplicated(keep=False)])

    return df.drop_duplicates(subset=chave).copy()


def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)

    destino = PRATA / "municipios.parquet"
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
    df = conferir_chave(df, chave="id")

    destino = salvar(df)

    registrar(
        origem,
        destino,
        antes,
        len(df),
        [
            "Espacos removidos",
            "Chave dos municipios verificada",
        ],
    )


if __name__ == "__main__":
    main()
