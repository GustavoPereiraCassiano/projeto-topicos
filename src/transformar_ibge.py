"""Prata da fonte secundaria: do JSON de municipios do IBGE para a tabela de UFs.

Entrada: dados/bronze/ibge/municipios_*.json (mais recente)
Saida:   dados/prata/ufs.parquet  (uma linha por UF)
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

import limpeza

RAIZ = Path(__file__).resolve().parent.parent
BRONZE = RAIZ / "dados" / "bronze" / "ibge"
PRATA = RAIZ / "dados" / "prata"
PADRAO = "municipios_*.json"


def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    print("lido:", caminho.name, len(dados), "municipios")
    return dados, caminho


def extrair_uf(municipio):
    """Acha a UF de um municipio.

    Caminho principal: microrregiao > mesorregiao > UF. Alguns municipios novos
    vem com microrregiao nula; para eles vale regiao-imediata > regiao-intermediaria > UF.
    """
    micro = municipio.get("microrregiao")
    if micro:
        uf = micro["mesorregiao"]["UF"]
        via = "microrregiao"
    else:
        uf = municipio["regiao-imediata"]["regiao-intermediaria"]["UF"]
        via = "regiao-imediata"
    return {
        "municipio_id": municipio["id"],
        "municipio_nome": municipio["nome"],
        "uf_id": uf["id"],
        "uf_sigla": uf["sigla"],
        "uf_nome": uf["nome"],
        "regiao_id": uf["regiao"]["id"],
        "regiao_sigla": uf["regiao"]["sigla"],
        "regiao_nome": uf["regiao"]["nome"],
        "_via": via,
    }


def achatar(dados):
    linhas = [extrair_uf(m) for m in dados]
    df = pd.DataFrame(linhas)
    via_fallback = int((df["_via"] != "microrregiao").sum())
    print("municipios sem microrregiao (usado o caminho alternativo):", via_fallback)
    return df.drop(columns="_via"), via_fallback


def montar_ufs(municipios):
    """Uma linha por UF, com a regiao e o numero de municipios."""
    ufs = (municipios
           .groupby(["uf_id", "uf_sigla", "uf_nome", "regiao_id", "regiao_sigla", "regiao_nome"],
                    as_index=False)
           .agg(n_municipios=("municipio_id", "nunique")))
    return ufs.sort_values("uf_sigla").reset_index(drop=True)


def conferir_ufs(ufs):
    print("UFs:", len(ufs))
    if len(ufs) != 27:
        print("ATENCAO: o Brasil tem 27 UFs (26 estados + DF); veio", len(ufs))
    if ufs["uf_sigla"].duplicated().any():
        raise ValueError("uf_sigla repetida: chave da tabela de UFs quebrada")


def converter_tipos(ufs):
    for c in ["uf_id", "regiao_id", "n_municipios"]:
        ufs[c] = pd.to_numeric(ufs[c], errors="raise").astype("int64")
    ufs["uf_sigla"] = ufs["uf_sigla"].str.upper()
    return ufs


def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "ufs.parquet"
    df.to_parquet(destino, index=False)
    print("salvo em:", destino, df.shape)
    return destino


def registrar(origem, destino, antes, depois, decisoes):
    limpeza.acrescentar_jsonl(PRATA / "proveniencia.jsonl", {
        "origem": origem.name,
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": decisoes,
        "transformado_em": datetime.now().isoformat(timespec="seconds"),
    })


def main():
    dados, origem = carregar()
    municipios, via_fallback = achatar(dados)
    espacos = limpeza.contar_com_espaco(municipios)
    municipios = limpeza.tirar_espacos(municipios)
    municipios, repetidos = limpeza.conferir_chave(municipios, "municipio_id")
    ufs = montar_ufs(municipios)
    conferir_ufs(ufs)
    ufs = converter_tipos(ufs)
    destino = salvar(ufs)
    registrar(origem, destino, len(dados), len(ufs), [
        f"JSON aninhado achatado; {via_fallback} municipios sem microrregiao usaram regiao-imediata",
        f"celulas com espaco sobrando por coluna: {espacos or 'nenhuma'}",
        f"municipio_id repetidos: {repetidos}",
        f"agregado de {len(municipios)} municipios em {len(ufs)} UFs (n_municipios por UF)",
    ])


if __name__ == "__main__":
    main()
