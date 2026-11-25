"""Prata: organiza o JSON de municípios do IBGE em formato Parquet."""
import json
import logging
from datetime import datetime

import pandas as pd

import config

log = logging.getLogger(__name__)


def carregar():
    arquivos = sorted(config.BRONZE_IBGE.glob("municipios_*.json"))

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum JSON encontrado em {config.BRONZE_IBGE}"
        )

    caminho = arquivos[-1]
    df = pd.read_json(caminho)

    log.info("municipios: arquivo lido %s, dimensoes %s",
             caminho.name, df.shape)
    log.debug("colunas: %s", df.columns.tolist())

    ausentes = df.isna().sum()
    for coluna, quantidade in ausentes[ausentes > 0].items():
        log.info("municipios: %s tem %s valores ausentes", coluna, quantidade)

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
        log.warning("municipios: coluna '%s' nao encontrada", chave)
        return df

    repetidas = int(df[chave].duplicated().sum())
    log.info("municipios: chaves repetidas: %s", repetidas)

    if repetidas:
        log.warning("municipios: %s chaves repetidas removidas", repetidas)

    return df.drop_duplicates(subset=chave).copy()


def salvar(df):
    config.PRATA_IBGE.mkdir(parents=True, exist_ok=True)

    destino = config.PRATA_IBGE / "municipios.parquet"
    df.to_parquet(destino, index=False)

    log.info("municipios: salvo %s, dimensoes finais %s",
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

    caminho = config.PRATA_IBGE / "proveniencia.jsonl"

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
    config.configurar_log()
    main()
