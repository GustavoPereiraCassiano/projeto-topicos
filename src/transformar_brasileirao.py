"""Prata: limpa o CSV do Brasileirão e cria o atributo pontos_mandante."""
import json
import logging
from datetime import datetime

import pandas as pd

import config
import limpeza

log = logging.getLogger(__name__)

PADRAO = "*.csv"


def carregar():
    arquivos = sorted(config.BRONZE_BRASILEIRAO.glob(PADRAO))

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum CSV encontrado em {config.BRONZE_BRASILEIRAO}"
        )

    # A Bronze nunca é alterada: a Prata sempre parte do arquivo mais recente
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)

    log.info("brasileirao: arquivo lido %s, dimensoes %s",
             caminho.name, df.shape)
    log.debug("colunas: %s", df.columns.tolist())

    ausentes = df.isna().sum()
    for coluna, quantidade in ausentes[ausentes > 0].items():
        log.info("brasileirao: %s tem %s valores ausentes", coluna, quantidade)

    return df, caminho


def conferir_duplicados(df):
    repetidas = int(df.duplicated().sum())
    log.info("brasileirao: linhas duplicadas: %s", repetidas)

    return df.drop_duplicates().copy()


def converter_placares(df):
    for coluna in ["mandante_Placar", "visitante_Placar"]:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(
                df[coluna], errors="coerce"
            )

    # Placar que não virou número gera pontos errados em silêncio
    invalidos = int(df[["mandante_Placar", "visitante_Placar"]].isna().sum().sum())
    if invalidos:
        log.warning("brasileirao: %s placares invalidos", invalidos)

    return df


def criar_pontos_mandante(df):
    df["pontos_mandante"] = 0

    vitoria = df["mandante_Placar"] > df["visitante_Placar"]
    empate = df["mandante_Placar"] == df["visitante_Placar"]

    df.loc[vitoria, "pontos_mandante"] = 3
    df.loc[empate, "pontos_mandante"] = 1

    return df


def salvar(df):
    config.PRATA_BRASILEIRAO.mkdir(parents=True, exist_ok=True)

    destino = config.PRATA_BRASILEIRAO / "brasileirao.parquet"
    df.to_parquet(destino, index=False)

    log.info("brasileirao: salvo %s, dimensoes finais %s",
             destino.name, df.shape)

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

    caminho = config.PRATA_BRASILEIRAO / "proveniencia.jsonl"

    with caminho.open("a", encoding="utf-8") as arquivo:
        arquivo.write(
            json.dumps(info, ensure_ascii=False) + "\n"
        )


def main():
    df, origem = carregar()
    antes = len(df)

    df = limpeza.tirar_espacos(df)
    df = conferir_duplicados(df)
    df = converter_placares(df)
    df = criar_pontos_mandante(df)

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
            "Atributo pontos_mandante criado a partir dos placares",
        ],
    )


if __name__ == "__main__":
    config.configurar_log()
    main()
