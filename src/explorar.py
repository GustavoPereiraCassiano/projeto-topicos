"""Perfilamento automatico das fontes da bronze (Aula 4).

Uso (a partir da raiz do projeto):
    python src/explorar.py              # todas as fontes
    python src/explorar.py brasileirao  # so uma
O relatorio HTML vai para relatorios/ (fora do Git: o codigo o refaz).
"""
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RELATORIOS = RAIZ / "relatorios"

# nome da fonte -> (pasta da bronze, padrao do arquivo)
FONTES = {
    "brasileirao": (RAIZ / "dados" / "bronze" / "brasileirao", "partidas_*.csv"),
    "ibge": (RAIZ / "dados" / "bronze" / "ibge", "municipios_*.json"),
}


def mais_recente(pasta, padrao):
    arquivos = sorted(pasta.glob(padrao))
    if not arquivos:
        raise FileNotFoundError(f"bronze vazia em {pasta}")
    return arquivos[-1]


def carregar(caminho):
    if caminho.suffix == ".json":
        # so para o perfil: achata o JSON aninhado em colunas
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        return pd.json_normalize(dados)
    return pd.read_csv(caminho)


def gerar(caminho):
    from data_profiling import ProfileReport  # pacote fg-data-profiling

    df = carregar(caminho)
    perfil = ProfileReport(df, title=caminho.name)
    RELATORIOS.mkdir(exist_ok=True)
    saida = RELATORIOS / f"{caminho.stem}.html"
    perfil.to_file(saida)
    return saida


def main():
    escolhidas = sys.argv[1:] or list(FONTES)
    for nome in escolhidas:
        pasta, padrao = FONTES[nome]
        caminho = mais_recente(pasta, padrao)
        print("perfilando:", caminho.name)
        print(gerar(caminho))


if __name__ == "__main__":
    main()
