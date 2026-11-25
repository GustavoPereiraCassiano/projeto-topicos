"""Prata: enriquece os jogos com o estado e a região do IBGE.

Junção: brasileirao.mandante_Estado = estados.UF, com how="left".
Saídas:
  - dados/prata/ibge/estados.parquet                    (um registro por UF)
  - dados/prata/brasileirao/brasileirao_enriquecido.parquet
"""
import json
import logging
from datetime import datetime

import pandas as pd

import config

log = logging.getLogger(__name__)


def montar_estados(municipios):
    """Uma linha por UF (sigla, nome e região), extraída dos municípios.

    Os dados do IBGE trazem a UF aninhada dentro de cada município
    (microrregiao > mesorregiao > UF). Aqui ela vira uma tabela.
    """
    estados = []

    for microrregiao in municipios["microrregiao"]:
        if not isinstance(microrregiao, dict):
            continue

        mesorregiao = microrregiao.get("mesorregiao")
        if not mesorregiao:
            continue

        uf = mesorregiao.get("UF")
        if not uf:
            continue

        regiao = uf.get("regiao") or {}

        estados.append({
            "UF": uf.get("sigla"),
            "estado": uf.get("nome"),
            "regiao": regiao.get("nome"),
        })

    estados = pd.DataFrame(estados).drop_duplicates().reset_index(drop=True)

    # A chave da junção precisa ser única do lado direito
    if estados["UF"].duplicated().any():
        raise ValueError("UF repetida na tabela de estados")

    return estados


def conferir_chaves(brasileirao, estados):
    """Compara as chaves antes de juntar: é a previsão do que a junção fará."""
    no_jogo = set(brasileirao["mandante_Estado"].dropna())
    no_ibge = set(estados["UF"].dropna())

    so_nos_jogos = sorted(no_jogo - no_ibge)
    log.info("chaves: %s UFs nos jogos, %s no IBGE, %s nos dois",
             len(no_jogo), len(no_ibge), len(no_jogo & no_ibge))
    if so_nos_jogos:
        log.warning("chaves: UFs dos jogos que o IBGE nao tem: %s", so_nos_jogos)

    return so_nos_jogos


def juntar(brasileirao, estados):
    # left: o que não casar aparece como ausente, em vez de sumir.
    # validate: o pandas recusa a junção se a UF se repetir no cadastro.
    return brasileirao.merge(
        estados[["UF", "regiao"]],
        left_on="mandante_Estado",
        right_on="UF",
        how="left",
        validate="many_to_one",
    )


def validar(brasileirao, enriquecido):
    """A conta que precisa fechar: mesmas linhas, e quantos não casaram."""
    sem_par = int(enriquecido["regiao"].isna().sum())

    log.info("juncao: %s linhas antes, %s depois, %s sem regiao",
             len(brasileirao), len(enriquecido), sem_par)

    if len(enriquecido) != len(brasileirao):
        raise ValueError(
            "a juncao mudou o numero de linhas: o grao nao foi preservado"
        )
    if sem_par:
        log.warning("juncao: %s jogos ficaram sem regiao", sem_par)

    return sem_par


def registrar(origens, destinos, linhas_antes, linhas_depois, sem_par):
    info = {
        "origem_esquerda": origens[0],
        "origem_direita": origens[1],
        "arquivo_prata": destinos[0],
        "arquivo_prata_estados": destinos[1],
        "linhas_antes": linhas_antes,
        "linhas_depois": linhas_depois,
        "sem_par": sem_par,
        "decisoes": [
            "Juncao pela esquerda: mandante_Estado = UF do IBGE",
            "validate=many_to_one: cada UF aparece uma vez no cadastro",
            "Atributo regiao trazido do IBGE",
        ],
        "transformado_em": datetime.now().isoformat(timespec="seconds"),
    }

    caminho = config.PRATA_BRASILEIRAO / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    # 1. Ler as duas tabelas já tratadas da Prata
    brasileirao = pd.read_parquet(
        config.PRATA_BRASILEIRAO / "brasileirao.parquet"
    )
    municipios = pd.read_parquet(config.PRATA_IBGE / "municipios.parquet")

    # 2. Uma linha por estado
    estados = montar_estados(municipios)
    config.PRATA_IBGE.mkdir(parents=True, exist_ok=True)
    estados.to_parquet(config.PRATA_IBGE / "estados.parquet", index=False)
    log.info("estados: %s UFs salvas em estados.parquet", len(estados))

    # 3. Conferir as chaves, juntar e validar
    conferir_chaves(brasileirao, estados)
    enriquecido = juntar(brasileirao, estados)
    sem_par = validar(brasileirao, enriquecido)

    # 4. Salvar na Prata
    config.PRATA_BRASILEIRAO.mkdir(parents=True, exist_ok=True)
    enriquecido.to_parquet(
        config.PRATA_BRASILEIRAO / "brasileirao_enriquecido.parquet",
        index=False,
    )
    log.info("brasileirao_enriquecido: %s linhas salvas", len(enriquecido))

    registrar(
        ("brasileirao.parquet", "municipios.parquet"),
        ("brasileirao_enriquecido.parquet", "estados.parquet"),
        len(brasileirao), len(enriquecido), sem_par,
    )


if __name__ == "__main__":
    config.configurar_log()
    main()
