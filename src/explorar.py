"""Perfil HTML das fontes. Roda fora do pipeline: python src/explorar.py"""
import logging

import pandas as pd
from data_profiling import ProfileReport

import config

log = logging.getLogger(__name__)

FONTES = [
    (config.BRONZE_BRASILEIRAO, "brasileirao_*.csv", pd.read_csv),
    (config.BRONZE_IBGE, "municipios_*.json", pd.read_json),
]


def mais_recente(pasta, padrao):
    arquivos = sorted(pasta.glob(padrao))

    if not arquivos:
        raise FileNotFoundError(f"bronze vazia: {pasta}")

    return arquivos[-1]


def gerar(caminho, leitor):
    df = leitor(caminho)
    perfil = ProfileReport(df, title=caminho.name)

    config.RELATORIOS.mkdir(exist_ok=True)
    saida = config.RELATORIOS / f"{caminho.stem}.html"

    perfil.to_file(saida)

    return saida


def main():
    for pasta, padrao, leitor in FONTES:
        caminho = mais_recente(pasta, padrao)
        log.info("perfilando: %s", caminho.name)
        log.info("relatorio: %s", gerar(caminho, leitor))


if __name__ == "__main__":
    config.configurar_log()
    main()
